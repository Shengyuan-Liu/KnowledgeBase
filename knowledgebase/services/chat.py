"""Conversation history, follow-up resolution and completed-exchange persistence."""

from collections.abc import AsyncGenerator
from contextlib import aclosing
from time import perf_counter
from uuid import uuid4

import anyio
from sqlalchemy.orm import Session, sessionmaker

from knowledgebase.config import DEFAULT_HISTORY_LIMIT
from knowledgebase.providers.llm import LLMClient
from knowledgebase.rag.query import resolve_question
from knowledgebase.schemas import ChatAnswer, ChatStreamEvent, ConversationAnswer, ConversationDetail, MessageInfo
from knowledgebase.services.rag import RagClient
from knowledgebase.storage.operations import (
    create_conversation, get_conversation, get_conversation_detail, get_messages,
    save_answer_snapshot, save_message,
)


class ConversationNotFoundError(LookupError):
    """The requested saved conversation does not exist."""


class ChatService:
    """Own conversation transactions around a reusable, independent RAG component."""

    def __init__(self, sessions: sessionmaker[Session], rag: RagClient, *,
                 resolver: LLMClient | None = None, history_limit: int = DEFAULT_HISTORY_LIMIT):
        self.sessions = sessions
        self.rag = rag
        self.resolver = resolver or rag.llm
        self.history_limit = history_limit

    def answer(self, question: str, *, conversation_id: str | None = None,
               file_ids: list[str] | None = None, retrieval_mode: str | None = None) -> ConversationAnswer:
        control = self.rag.request_control(retrieval_mode)
        resolver = self.resolver.bounded(control.generation_limits(resolver=True)) if control else self.resolver
        history = self._load_history(conversation_id)
        resolved = resolve_question(question, history, resolver)
        result = self.rag.answer(question, retrieval_question=resolved, file_ids=file_ids,
                                 retrieval_mode=retrieval_mode, control=control)
        if control:
            control.remaining()
        return self._save_exchange(question, resolved, result, conversation_id)

    async def stream(self, question: str, request_id: str, *, conversation_id: str | None = None,
                     file_ids: list[str] | None = None,
                     retrieval_mode: str | None = None) -> AsyncGenerator[ChatStreamEvent]:
        """Validate history before HTTP streaming and persist only the final answer."""
        control = self.rag.request_control(retrieval_mode)
        resolver = self.resolver.bounded(control.generation_limits(resolver=True)) if control else self.resolver
        history = await anyio.to_thread.run_sync(self._load_history, conversation_id)

        async def events():
            def event(kind, **data):
                return ChatStreamEvent(event=kind, request_id=request_id, data=data)

            started = perf_counter()
            yield event("start", conversation_id=conversation_id)
            try:
                if control:
                    yield event("progress", stage="planning", message="Planning the search…")
                    resolved = await control.run_search(resolve_question, question, history, resolver)
                else:
                    resolved = await anyio.to_thread.run_sync(
                        resolve_question, question, history, resolver, abandon_on_cancel=True,
                    )
                async with aclosing(self.rag.stream(question, request_id, retrieval_question=resolved,
                    file_ids=file_ids, retrieval_mode=retrieval_mode, control=control)) as stream:
                    async for item in stream:
                        if isinstance(item, ChatAnswer):
                            yield event("debug", retrieval_question=resolved, distance_metric="cosine",
                                        elapsed_seconds=perf_counter() - started)
                            await anyio.lowlevel.checkpoint()
                            if control:
                                control.remaining()
                            saved = await anyio.to_thread.run_sync(
                                self._save_exchange, question, resolved, item, conversation_id,
                            )
                            yield event("complete", **saved.model_dump(mode="json"))
                        else:
                            yield item
            except TimeoutError:
                yield event("error", message="The planned request timed out. Please retry or narrow the question.")
            except Exception:
                yield event("error", message="Answer processing failed.")
            finally:
                if control:
                    control.cancelled.set()

        return events()

    def _load_history(self, conversation_id: str | None) -> list[MessageInfo]:
        if self.history_limit < 1:
            raise ValueError("history_limit must be positive.")
        if conversation_id is None:
            return []
        with self.sessions() as session:
            if get_conversation(session, conversation_id) is None:
                raise ConversationNotFoundError(f"Conversation not found: {conversation_id}")
            return get_messages(session, conversation_id, limit=self.history_limit)

    def _save_exchange(self, question: str, resolved: str, result: ChatAnswer,
                       conversation_id: str | None) -> ConversationAnswer:
        with self.sessions.begin() as session:
            if conversation_id is None:
                conversation_id = uuid4().hex
                create_conversation(session, conversation_id)
            save_message(session, conversation_id, "user", question)
            message = save_message(session, conversation_id, "assistant", result.answer)
            save_answer_snapshot(session, message.message_id, resolved, result)
        return ConversationAnswer(
            answer=result.answer, sources=result.sources, citation_check=result.citation_check,
            retrieval=result.retrieval, conversation_id=conversation_id, message_id=message.message_id,
            question=question, retrieval_question=resolved,
        )

    def get_conversation(self, conversation_id: str) -> ConversationDetail:
        with self.sessions() as session:
            conversation = get_conversation_detail(session, conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(f"Conversation not found: {conversation_id}")
        return conversation


from knowledgebase.config import DEFAULT_TOP_K, DEFAULT_EVIDENCE_MAX_TOKENS, DEFAULT_CHUNK_TOKENIZER, RetrievalOptions, PlanningOptions
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import StreamingLLMClient
from knowledgebase.providers.reranker import RerankerClient
from knowledgebase.providers.planner import PlannerClient
from knowledgebase.services.planning import RequestControl
from knowledgebase.storage.vectordb import ChromaStore
from knowledgebase.rag.retrieval import _configured_retriever


def _configured_rag(sessions, embeddings, store, llm, streaming=None, *, top_k=DEFAULT_TOP_K,
                    evidence_max_tokens=DEFAULT_EVIDENCE_MAX_TOKENS, encoding_name=DEFAULT_CHUNK_TOKENIZER,
                    retrieval_options=None, reranker_client=None, planner_client=None, planning_options=None):
    retriever = _configured_retriever(embeddings, store, top_k, evidence_max_tokens=evidence_max_tokens,
        encoding_name=encoding_name, retrieval_options=retrieval_options, reranker_client=reranker_client)
    return RagClient(sessions, retriever, llm, streaming, planner=planner_client, planning_options=planning_options,
                     retrieval_mode="planned" if planner_client else "single")


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
    rag = _configured_rag(session_factory, embedding_client, vector_store, llm_client,
        top_k=top_k, evidence_max_tokens=evidence_max_tokens, encoding_name=encoding_name,
        retrieval_options=retrieval_options, reranker_client=reranker_client,
        planner_client=planner_client, planning_options=planning_options)
    return rag.answer(question, retrieval_question=retrieval_question, file_ids=file_ids, control=_control)


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
    rag = _configured_rag(session_factory, embedding_client, vector_store, llm_client,
        top_k=top_k, evidence_max_tokens=evidence_max_tokens, encoding_name=encoding_name,
        retrieval_options=retrieval_options, reranker_client=reranker_client,
        planner_client=planner_client, planning_options=planning_options)
    chat = ChatService(session_factory, rag, resolver=resolver_client, history_limit=history_limit)
    return chat.answer(question, conversation_id=conversation_id, file_ids=file_ids)


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
    rag = _configured_rag(session_factory, embedding_client, vector_store, llm_client, streaming_client,
        top_k=top_k, evidence_max_tokens=evidence_max_tokens, encoding_name=encoding_name,
        retrieval_options=retrieval_options, reranker_client=reranker_client,
        planner_client=planner_client, planning_options=planning_options)
    chat = ChatService(session_factory, rag, resolver=resolver_client, history_limit=history_limit)
    return await chat.stream(question, request_id, conversation_id=conversation_id, file_ids=file_ids)
