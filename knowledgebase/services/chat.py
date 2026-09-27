"""Coordinate single-turn and conversational knowledge-base answers."""

from bisect import bisect_right
from collections.abc import AsyncGenerator
from contextlib import aclosing
import re
from time import perf_counter
from uuid import uuid4

import anyio

from sqlalchemy.orm import Session, sessionmaker

from knowledgebase.config import (
    DEFAULT_TOP_K, DEFAULT_HISTORY_LIMIT, DEFAULT_EVIDENCE_MAX_TOKENS, DEFAULT_CHUNK_TOKENIZER,
    RetrievalOptions, PlanningOptions,
)
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient, StreamingLLMClient
from knowledgebase.providers.reranker import RerankerClient
from knowledgebase.providers.planner import PlannerClient
from knowledgebase.services.planning import RequestControl, PreparedPlanning, prepare_planning, NARROWING_MESSAGE
from knowledgebase.services.hops import HopController
from knowledgebase.rag.planned_retrieval import retrieve_plan
from knowledgebase.rag.context import build_context
from knowledgebase.rag.citations import validate_citations
from knowledgebase.rag.generation import generate_answer, stream_answer
from knowledgebase.rag.query import resolve_question
from knowledgebase.rag.retrieval import retrieve_evidence
from knowledgebase.schemas import (
    AnswerSource, ChatAnswer, ChatStreamEvent, ConversationAnswer, MessageInfo,
    RetrievedChunk, RetrievedEvidence, RetrievalDiagnostics, StructuredChunk,
)
from knowledgebase.storage.operations import (
    create_conversation,
    get_conversation,
    get_document_source,
    get_messages,
    save_answer_snapshot,
    save_message,
)
from knowledgebase.storage.vectordb import ChromaStore


class ConversationNotFoundError(LookupError):
    """The requested saved conversation does not exist."""


def answer_question(
    question: str,
    session_factory: sessionmaker[Session],
    embedding_client: EmbeddingClient,
    vector_store: ChromaStore,
    llm_client: LLMClient,
    top_k: int = DEFAULT_TOP_K,
    *, retrieval_question: str | None = None,
    evidence_max_tokens: int = DEFAULT_EVIDENCE_MAX_TOKENS,
    encoding_name: str = DEFAULT_CHUNK_TOKENIZER,
    retrieval_options: RetrievalOptions | None = None,
    reranker_client: RerankerClient | None = None,
    file_ids: list[str] | None = None,
    planner_client: PlannerClient | None = None,
    planning_options: PlanningOptions | None = None,
    _control: RequestControl | None = None,
) -> ChatAnswer:
    """Return an answer and sources in the same order used by the prompt.

    The service owns its read session and closes it before generation. Sources
    include every retrieved excerpt, regardless of which ones the model cites.
    Source IDs are one-based and local to this answer.
    """
    control = _control or (RequestControl(planning_options or PlanningOptions(), encoding_name) if planner_client else None)
    prepared = prepare_planning(question, retrieval_question or question, session_factory, file_ids, planner_client, control) if planner_client else None
    if control:
        embedding_client = embedding_client.bounded(control.before_answer)
        llm_client = llm_client.bounded(control.generation_limits())
    hops = None
    if prepared and prepared.plan and prepared.allowed_file_ids and (prepared.plan.dependencies or control.options.sufficiency_enabled):
        hops = HopController(prepared, session_factory, embedding_client, vector_store, planner_client, control,
            top_k=top_k, evidence_max_tokens=evidence_max_tokens, encoding_name=encoding_name,
            retrieval_options=retrieval_options, reranker_client=reranker_client, file_ids=file_ids)
        while not hops.finished:
            hops.step()
            if hops.needs_assessment:
                hops.assess()
    chunks, sources, diagnostics = _retrieve_evidence(
        retrieval_question or question, session_factory, embedding_client, vector_store, top_k,
        evidence_max_tokens, encoding_name, retrieval_options, reranker_client,
        file_ids, question, prepared, control, hops,
    )
    scope = diagnostics.document_scope
    message = scope.message if scope and scope.status != "resolved" else (diagnostics.planning or {}).get("message")
    answer = (message if message else
              generate_answer(question, chunks, llm_client, retrieval_question=retrieval_question,
                              assessment=(diagnostics.planning or {}).get("assessment")))
    if control:
        control.remaining()
    return ChatAnswer(
        answer=answer, sources=sources,
        citation_check=validate_citations(answer, sources), retrieval=diagnostics,
    )


def _retrieve_evidence(
    question: str, session_factory: sessionmaker[Session], embedding_client: EmbeddingClient,
    vector_store: ChromaStore, top_k: int, evidence_max_tokens: int, encoding_name: str,
    retrieval_options: RetrievalOptions | None,
    reranker_client: RerankerClient | None,
    file_ids: list[str] | None = None,
    scope_question: str | None = None,
    prepared: PreparedPlanning | None = None,
    control: RequestControl | None = None,
    hops: HopController | None = None,
) -> tuple[list[RetrievedChunk], list[AnswerSource], RetrievalDiagnostics]:
    started = perf_counter()
    with session_factory() as session:
        trace = None
        if prepared is not None:
            control.before_answer()
            if hops is not None:
                evidence, trace = hops.result.evidence, hops.result.trace.model_dump(mode="json")
            elif prepared.plan is None:
                evidence = RetrievedEvidence(chunks=[], diagnostics=RetrievalDiagnostics(
                    max_tokens=evidence_max_tokens, tokenizer=encoding_name,
                    options=retrieval_options or RetrievalOptions(), top_k=top_k,
                ))
            else:
                planned = retrieve_plan(
                    prepared.plan, session, embedding_client, vector_store, top_k=top_k,
                    evidence_max_tokens=evidence_max_tokens, encoding_name=encoding_name,
                    retrieval_options=retrieval_options, reranker_client=reranker_client,
                    file_ids=file_ids, allowed_file_ids=prepared.allowed_file_ids, checkpoint=control.before_answer,
                )
                evidence, trace = planned.evidence, planned.trace.model_dump(mode="json")
            evidence.diagnostics.planning = {
                "version": 3 if hops and hops.assessment else 2 if hops else 1, "planner": prepared.record, "trace": trace,
                **({"hops": hops.trace} if hops else {}),
                **({"assessment": hops.assessment} if hops and hops.assessment else {}),
                "limits": control.options.model_dump(),
                "message": NARROWING_MESSAGE if prepared.plan is None else None,
                "context": build_context(evidence.chunks),
            }
            control.before_answer()
        else:
            evidence = retrieve_evidence(
                question, session, embedding_client, vector_store, top_k=top_k,
                evidence_max_tokens=evidence_max_tokens, encoding_name=encoding_name,
                retrieval_options=retrieval_options, reranker_client=reranker_client,
                file_ids=file_ids, scope_question=scope_question,
            )
        chunks = evidence.chunks
        line_starts = {}
        for file_id in {item.chunk.file_id for item in chunks}:
            document = get_document_source(session, file_id)
            if document is not None and document.source_format != "pdf":
                line_starts[file_id] = [0, *(m.end() for m in re.finditer(r"\r\n|\r|\n", document.text))]
        sources = [
            AnswerSource(
                source_id=number, pdf=item.pdf,
                file_id=item.chunk.file_id,
                file_name=item.file_name,
                document_labels=item.document_labels,
                chunk_id=item.chunk.chunk_id,
                text=item.chunk.text,
                distance=item.distance, fusion=item.fusion, rerank=item.rerank,
                parent_id=item.parent_id, matched_child_ids=item.matched_child_ids,
                start_offset=item.chunk.start_offset, end_offset=item.chunk.end_offset,
                start_line=bisect_right(line_starts[item.chunk.file_id], item.chunk.start_offset)
                    if item.chunk.file_id in line_starts else None,
                end_line=bisect_right(line_starts[item.chunk.file_id], item.chunk.end_offset - 1)
                    if item.chunk.file_id in line_starts else None,
                **(item.chunk.model_dump(include={
                    "heading_path", "source_block_indices", "token_count", "tokenizer", "max_tokens",
                }) if isinstance(item.chunk, StructuredChunk) else {}),
            )
            for number, item in enumerate(chunks, start=1)
        ]

    evidence.diagnostics.retrieval_seconds = perf_counter() - started + (hops.retrieval_seconds if hops else 0)
    return chunks, sources, evidence.diagnostics


def answer_in_conversation(
    question: str,
    session_factory: sessionmaker[Session],
    embedding_client: EmbeddingClient,
    vector_store: ChromaStore,
    llm_client: LLMClient,
    conversation_id: str | None = None,
    top_k: int = DEFAULT_TOP_K,
    history_limit: int = DEFAULT_HISTORY_LIMIT,
    *, resolver_client: LLMClient | None = None,
    evidence_max_tokens: int = DEFAULT_EVIDENCE_MAX_TOKENS,
    encoding_name: str = DEFAULT_CHUNK_TOKENIZER,
    retrieval_options: RetrievalOptions | None = None,
    reranker_client: RerankerClient | None = None,
    file_ids: list[str] | None = None,
    planner_client: PlannerClient | None = None,
    planning_options: PlanningOptions | None = None,
) -> ConversationAnswer:
    """Resolve a follow-up, retrieve fresh evidence, and save a completed exchange.

    Omit conversation_id to start a new conversation. A supplied ID must exist.
    Model calls run outside history/write sessions. Only successful exchanges
    are saved, with the original question, answer, and evidence in one transaction.
    """
    control = RequestControl(planning_options or PlanningOptions(), encoding_name) if planner_client else None
    if control:
        resolver_client = (resolver_client or llm_client).bounded(control.generation_limits(resolver=True))
    history = _load_history(session_factory, conversation_id, history_limit)
    retrieval_question = resolve_question(question, history, resolver_client or llm_client)
    result = answer_question(
        question, session_factory, embedding_client, vector_store,
        llm_client, top_k=top_k, retrieval_question=retrieval_question,
        evidence_max_tokens=evidence_max_tokens, encoding_name=encoding_name,
        retrieval_options=retrieval_options, reranker_client=reranker_client,
        file_ids=file_ids, planner_client=planner_client, planning_options=planning_options, _control=control,
    )

    if control:
        control.remaining()
    return _save_exchange(question, retrieval_question, result, session_factory, conversation_id)


def _load_history(
    session_factory: sessionmaker[Session], conversation_id: str | None, history_limit: int,
) -> list[MessageInfo]:
    if history_limit < 1:
        raise ValueError("history_limit must be positive.")
    if conversation_id is None:
        return []
    with session_factory() as session:
        if get_conversation(session, conversation_id) is None:
            raise ConversationNotFoundError(f"Conversation not found: {conversation_id}")
        return get_messages(session, conversation_id, limit=history_limit)


def _save_exchange(
    question: str, retrieval_question: str, result: ChatAnswer,
    session_factory: sessionmaker[Session], conversation_id: str | None,
) -> ConversationAnswer:
    with session_factory.begin() as session:
        if conversation_id is None:
            conversation_id = uuid4().hex
            create_conversation(session, conversation_id)
        save_message(session, conversation_id, "user", question)
        message = save_message(session, conversation_id, "assistant", result.answer)
        save_answer_snapshot(session, message.message_id, retrieval_question, result)

    return ConversationAnswer(
        answer=result.answer, sources=result.sources,
        citation_check=result.citation_check, retrieval=result.retrieval,
        conversation_id=conversation_id, message_id=message.message_id,
        question=question, retrieval_question=retrieval_question,
    )


async def stream_answer_in_conversation(
    question: str,
    request_id: str,
    session_factory: sessionmaker[Session],
    embedding_client: EmbeddingClient,
    vector_store: ChromaStore,
    llm_client: LLMClient,
    streaming_client: StreamingLLMClient,
    conversation_id: str | None = None,
    top_k: int = DEFAULT_TOP_K,
    history_limit: int = DEFAULT_HISTORY_LIMIT,
    *, resolver_client: LLMClient | None = None,
    evidence_max_tokens: int = DEFAULT_EVIDENCE_MAX_TOKENS,
    encoding_name: str = DEFAULT_CHUNK_TOKENIZER,
    retrieval_options: RetrievalOptions | None = None,
    reranker_client: RerankerClient | None = None,
    file_ids: list[str] | None = None,
    planner_client: PlannerClient | None = None,
    planning_options: PlanningOptions | None = None,
) -> AsyncGenerator[ChatStreamEvent]:
    """Validate the conversation before streaming; persist only a completed answer.

    Cancellation before saving leaves history unchanged. The final short database
    transaction is shielded; a disconnect after commit can lose delivery of the
    completion event, but never stores a partial answer.
    """
    control = RequestControl(planning_options or PlanningOptions(), encoding_name) if planner_client else None
    if control:
        resolver_client = (resolver_client or llm_client).bounded(control.generation_limits(resolver=True))
        embedding_client = embedding_client.bounded(control.before_answer)
        streaming_client = streaming_client.bounded(control.generation_limits())
    history = await anyio.to_thread.run_sync(_load_history, session_factory, conversation_id, history_limit)

    async def events():
        def event(kind, **data):
            return ChatStreamEvent(event=kind, request_id=request_id, data=data)

        started = perf_counter()
        yield event("start", conversation_id=conversation_id)
        try:
            prepared = None
            if control:
                yield event("progress", stage="planning", message="Planning the search…")
                retrieval_question = await control.run_search(resolve_question, question, history, resolver_client)
                prepared = await control.run_search(prepare_planning, question, retrieval_question, session_factory,
                                                    file_ids, planner_client, control)
                hops = None
                if prepared.plan and prepared.allowed_file_ids and (prepared.plan.dependencies or control.options.sufficiency_enabled):
                    hops = HopController(prepared, session_factory, embedding_client, vector_store, planner_client, control,
                        top_k=top_k, evidence_max_tokens=evidence_max_tokens, encoding_name=encoding_name,
                        retrieval_options=retrieval_options, reranker_client=reranker_client, file_ids=file_ids)
                    while not hops.finished:
                        yield event("progress", stage="retrieving", message=f"Searching round {hops.round_index + 1}…")
                        await control.run_search(hops.step)
                        if hops.needs_assessment:
                            yield event("progress", stage="assessing", message="Checking evidence…")
                            await control.run_search(hops.assess)
                if hops is None:
                    yield event("progress", stage="retrieving", message="Searching for each answer point…")
                chunks, sources, diagnostics = await control.run_search(
                    _retrieve_evidence, retrieval_question, session_factory, embedding_client,
                    vector_store, top_k, evidence_max_tokens, encoding_name, retrieval_options, reranker_client,
                    file_ids, question, prepared, control, hops,
                )
            else:
                retrieval_question = await anyio.to_thread.run_sync(
                    resolve_question, question, history, resolver_client or llm_client, abandon_on_cancel=True,
                )
                chunks, sources, diagnostics = await anyio.to_thread.run_sync(
                    _retrieve_evidence, retrieval_question, session_factory, embedding_client,
                    vector_store, top_k, evidence_max_tokens, encoding_name, retrieval_options, reranker_client,
                    file_ids, question, abandon_on_cancel=True,
                )
            yield event("sources", sources=[source.model_dump() for source in sources],
                        **({"retrieval": diagnostics.model_dump(mode="json")} if control else {}))
            parts = []
            scope = diagnostics.document_scope
            message = scope.message if scope and scope.status != "resolved" else (diagnostics.planning or {}).get("message")
            if message:
                parts.append(message)
                yield event("answer_delta", delta=message)
            else:
                async with aclosing(stream_answer(question, chunks, streaming_client, retrieval_question=retrieval_question,
                    assessment=(diagnostics.planning or {}).get("assessment"))) as stream:
                    async for delta in stream:
                        parts.append(delta)
                        yield event("answer_delta", delta=delta)
            answer = "".join(parts)
            result = ChatAnswer(
                answer=answer, sources=sources,
                citation_check=validate_citations(answer, sources), retrieval=diagnostics,
            )
            yield event("debug", retrieval_question=retrieval_question, distance_metric="cosine",
                        elapsed_seconds=perf_counter() - started)
            # Let a queued disconnect cancel this turn before beginning the commit.
            await anyio.lowlevel.checkpoint()
            if control:
                control.remaining()
            saved = await anyio.to_thread.run_sync(
                _save_exchange, question, retrieval_question, result, session_factory, conversation_id,
            )
            yield event("complete", **saved.model_dump(mode="json"))
        except TimeoutError:
            yield event("error", message="The planned request timed out. Please retry or narrow the question.")
        except Exception:
            yield event("error", message="Answer processing failed.")
        finally:
            if control:
                control.cancelled.set()

    return events()
