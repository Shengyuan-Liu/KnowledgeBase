"""Compose retrieval, planning and grounded answers without conversation persistence."""

import re
from bisect import bisect_right
from collections.abc import AsyncGenerator
from contextlib import aclosing
from functools import partial
from time import perf_counter

import anyio
from sqlalchemy.orm import Session, sessionmaker

from knowledgebase.config import PlanningOptions
from knowledgebase.providers.llm import LLMClient, StreamingLLMClient
from knowledgebase.providers.planner import PlannerClient
from knowledgebase.rag.citations import validate_citations
from knowledgebase.rag.context import build_context
from knowledgebase.rag.generation import generate_answer, stream_answer
from knowledgebase.rag.retrieval import Retriever, resolve_ready_scope
from knowledgebase.schemas import (
    AnswerSource,
    ChatAnswer,
    ChatStreamEvent,
    RetrievalDiagnostics,
    RetrievedChunk,
    RetrievedEvidence,
    direct_plan,
)
from knowledgebase.services.hops import HopController
from knowledgebase.services.planning import (
    NARROWING_MESSAGE,
    PreparedPlanning,
    RequestControl,
)
from knowledgebase.storage.operations import get_source_texts


class RagClient:
    """Reuse dependencies while keeping plans, evidence and deadlines per request."""

    def __init__(
        self,
        sessions: sessionmaker[Session],
        retriever: Retriever,
        llm: LLMClient,
        streaming_llm: StreamingLLMClient | None = None,
        *,
        planner: PlannerClient | None = None,
        planning_options: PlanningOptions | None = None,
        retrieval_mode: str = "single",
    ):
        self.sessions = sessions
        self.retriever = retriever
        self.llm = llm
        self.streaming_llm = streaming_llm
        self.planner = planner
        self.planning_options = planning_options or PlanningOptions()
        self.retrieval_mode = retrieval_mode

    def request_control(self, retrieval_mode: str | None = None) -> RequestControl | None:
        if (retrieval_mode or self.retrieval_mode) == "single":
            return None
        if self.planner is None:
            raise RuntimeError("The planner is not configured.")
        return RequestControl(self.planning_options, self.retriever.encoding_name)

    def _prepare_plan(self, question, resolved, file_ids, control):
        control.before_answer()
        with self.sessions() as session:
            ready, scope = resolve_ready_scope(
                resolved, session, file_ids=file_ids, scope_question=question
            )
        if not ready:
            return PreparedPlanning(
                direct_plan(question, resolved_question=resolved),
                [],
                None,
                scope if scope and scope.status != "resolved" else None,
            )
        generated = self.planner.plan(question, resolved, control.before_answer)
        control.before_answer()
        return PreparedPlanning(generated.plan, list(ready), generated.record)

    def _new_hops(self, prepared, retriever, control, file_ids):
        if (
            prepared
            and prepared.plan
            and prepared.allowed_file_ids
            and (prepared.plan.dependencies or control.options.sufficiency_enabled)
        ):
            return HopController(
                prepared, self.sessions, retriever, self.planner, control, file_ids=file_ids
            )
        return None

    def answer(
        self,
        question: str,
        *,
        retrieval_question: str | None = None,
        file_ids: list[str] | None = None,
        retrieval_mode: str | None = None,
        control: RequestControl | None = None,
    ) -> ChatAnswer:
        control = control or self.request_control(retrieval_mode)
        resolved = retrieval_question or question
        prepared = self._prepare_plan(question, resolved, file_ids, control) if control else None
        retriever = self.retriever.bounded(control.before_answer) if control else self.retriever
        llm = self.llm.bounded(control.generation_limits()) if control else self.llm
        hops = self._new_hops(prepared, retriever, control, file_ids)
        if hops:
            while not hops.finished:
                hops.step()
                if hops.needs_assessment:
                    hops.assess()
        chunks, sources, diagnostics = self._prepare_evidence(
            question,
            resolved,
            retriever,
            file_ids,
            prepared,
            control,
            hops,
        )
        message = self._scope_message(diagnostics)
        answer = (
            message
            if message
            else generate_answer(
                question,
                chunks,
                llm,
                retrieval_question=retrieval_question,
                assessment=(diagnostics.planning or {}).get("assessment"),
            )
        )
        if control:
            control.remaining()
        return self._answer_result(answer, sources, diagnostics)

    async def stream(
        self,
        question: str,
        request_id: str,
        *,
        retrieval_question: str | None = None,
        file_ids: list[str] | None = None,
        retrieval_mode: str | None = None,
        control: RequestControl | None = None,
    ) -> AsyncGenerator[ChatStreamEvent | ChatAnswer]:
        """Yield RAG events and a final unsaved ChatAnswer; the caller owns persistence."""
        control = control or self.request_control(retrieval_mode)
        resolved = retrieval_question or question
        retriever = self.retriever.bounded(control.before_answer) if control else self.retriever
        streaming = (
            self.streaming_llm.bounded(control.generation_limits())
            if control
            else self.streaming_llm
        )

        def event(kind, **data):
            return ChatStreamEvent(event=kind, request_id=request_id, data=data)

        try:
            prepared = None
            hops = None
            if control:
                prepared = await control.run_search(
                    self._prepare_plan, question, resolved, file_ids, control
                )
                hops = self._new_hops(prepared, retriever, control, file_ids)
                if hops:
                    while not hops.finished:
                        yield event(
                            "progress",
                            stage="retrieving",
                            message=f"Searching round {hops.round_index + 1}…",
                        )
                        await control.run_search(hops.step)
                        if hops.needs_assessment:
                            yield event("progress", stage="assessing", message="Checking evidence…")
                            await control.run_search(hops.assess)
                else:
                    yield event(
                        "progress", stage="retrieving", message="Searching for each answer point…"
                    )
                chunks, sources, diagnostics = await control.run_search(
                    self._prepare_evidence,
                    question,
                    resolved,
                    retriever,
                    file_ids,
                    prepared,
                    control,
                    hops,
                )
            else:
                chunks, sources, diagnostics = await anyio.to_thread.run_sync(
                    partial(self._prepare_evidence, question, resolved, retriever, file_ids),
                    abandon_on_cancel=True,
                )
            yield event(
                "sources",
                sources=[source.model_dump() for source in sources],
                **({"retrieval": diagnostics.model_dump(mode="json")} if control else {}),
            )
            parts = []
            message = self._scope_message(diagnostics)
            if message:
                parts.append(message)
                yield event("answer_delta", delta=message)
            else:
                async with aclosing(
                    stream_answer(
                        question,
                        chunks,
                        streaming,
                        retrieval_question=retrieval_question,
                        assessment=(diagnostics.planning or {}).get("assessment"),
                    )
                ) as stream:
                    async for delta in stream:
                        parts.append(delta)
                        yield event("answer_delta", delta=delta)
            yield self._answer_result("".join(parts), sources, diagnostics)
        finally:
            if control:
                control.cancelled.set()

    @staticmethod
    def _scope_message(diagnostics):
        scope = diagnostics.document_scope
        return (
            scope.message
            if scope and scope.status != "resolved"
            else (diagnostics.planning or {}).get("message")
        )

    @staticmethod
    def _answer_result(answer, sources, diagnostics):
        return ChatAnswer(
            answer=answer,
            sources=sources,
            citation_check=validate_citations(answer, sources),
            retrieval=diagnostics,
        )

    def _prepare_evidence(
        self, question, resolved, retriever, file_ids=None, prepared=None, control=None, hops=None
    ):
        started = perf_counter()
        with self.sessions() as session:
            trace = None
            if prepared is not None:
                control.before_answer()
                if hops is not None:
                    evidence, trace = (
                        hops.result.evidence,
                        hops.result.trace.model_dump(mode="json"),
                    )
                elif prepared.scope_failure is not None or prepared.plan is None:
                    evidence = RetrievedEvidence(
                        chunks=[],
                        diagnostics=RetrievalDiagnostics(
                            max_tokens=retriever.evidence_max_tokens,
                            tokenizer=retriever.encoding_name,
                            options=retriever.options,
                            top_k=retriever.top_k,
                            document_scope=prepared.scope_failure,
                        ),
                    )
                else:
                    planned = retriever.retrieve_plan(
                        prepared.plan,
                        session,
                        file_ids=file_ids,
                        allowed_file_ids=prepared.allowed_file_ids,
                        checkpoint=control.before_answer,
                    )
                    evidence, trace = planned.evidence, planned.trace.model_dump(mode="json")
                evidence.diagnostics.planning = {
                    "version": 3 if hops and hops.assessment else 2 if hops else 1,
                    "planner": prepared.record,
                    "trace": trace,
                    **({"hops": hops.trace} if hops else {}),
                    **({"assessment": hops.assessment} if hops and hops.assessment else {}),
                    "limits": control.options.model_dump(),
                    "message": NARROWING_MESSAGE if prepared.plan is None else None,
                    "context": build_context(evidence.chunks),
                }
                control.before_answer()
            else:
                evidence = retriever.retrieve(
                    resolved, session, file_ids=file_ids, scope_question=question
                )
            sources = self._build_sources(evidence.chunks, session)
        evidence.diagnostics.retrieval_seconds = (
            perf_counter() - started + (hops.retrieval_seconds if hops else 0)
        )
        return evidence.chunks, sources, evidence.diagnostics

    @staticmethod
    def _build_sources(chunks: list[RetrievedChunk], session: Session) -> list[AnswerSource]:
        text_files = list({item.chunk.file_id for item in chunks if item.pdf is None})
        line_starts = {
            file_id: [0, *(m.end() for m in re.finditer(r"\r\n|\r|\n", text))]
            for file_id, text in get_source_texts(session, text_files).items()
        }
        return [
            AnswerSource(
                source_id=number,
                pdf=item.pdf,
                file_id=item.chunk.file_id,
                file_name=item.file_name,
                document_labels=item.document_labels,
                chunk_id=item.chunk.chunk_id,
                text=item.chunk.text,
                distance=item.distance,
                fusion=item.fusion,
                rerank=item.rerank,
                parent_id=item.parent_id,
                matched_child_ids=item.matched_child_ids,
                start_offset=item.chunk.start_offset,
                end_offset=item.chunk.end_offset,
                start_line=bisect_right(line_starts[item.chunk.file_id], item.chunk.start_offset)
                if item.chunk.file_id in line_starts
                else None,
                end_line=bisect_right(line_starts[item.chunk.file_id], item.chunk.end_offset - 1)
                if item.chunk.file_id in line_starts
                else None,
                **item.chunk.model_dump(
                    include={
                        "heading_path",
                        "source_block_indices",
                        "token_count",
                        "tokenizer",
                        "max_tokens",
                    }
                ),
            )
            for number, item in enumerate(chunks, start=1)
        ]
