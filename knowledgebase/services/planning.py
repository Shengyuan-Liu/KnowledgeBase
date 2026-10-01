"""Bound planned requests and prepare plans outside storage transactions."""

from dataclasses import dataclass
from threading import Event
from time import monotonic

import anyio

from knowledgebase.config import PlanningOptions
from knowledgebase.providers.limits import GenerationLimits
from knowledgebase.providers.planner import PlannerClient
from knowledgebase.rag.planning import RetrievalPlan, direct_plan
from knowledgebase.rag.retrieval import resolve_ready_scope
from knowledgebase.schemas import DocumentScope

NARROWING_MESSAGE = "This question needs more than six answer points or searches. Please narrow it or split it into smaller questions."


class RequestControl:
    def __init__(self, options: PlanningOptions, encoding_name: str):
        self.options, self.encoding_name = options, encoding_name
        self.deadline = monotonic() + options.request_timeout_seconds
        self.cancelled = Event()

    def remaining(self) -> float:
        if self.cancelled.is_set():
            raise TimeoutError("The planned request was cancelled.")
        remaining = self.deadline - monotonic()
        if remaining <= 0:
            raise TimeoutError("The planned request deadline was reached.")
        return remaining

    def before_answer(self) -> float:
        remaining = self.remaining() - self.options.answer_reserve_seconds
        if remaining <= 0:
            raise TimeoutError("The search deadline was reached before the final-answer reserve.")
        return remaining

    def generation_limits(self, *, resolver: bool = False) -> GenerationLimits:
        return GenerationLimits(
            self.before_answer if resolver else self.remaining,
            self.options.max_input_tokens if resolver else self.options.answer_max_input_tokens,
            self.options.max_output_tokens if resolver else self.options.answer_max_output_tokens,
            self.encoding_name,
        )

    async def run_search(self, function, *args):
        with anyio.fail_after(self.before_answer()):
            return await anyio.to_thread.run_sync(function, *args, abandon_on_cancel=True)


@dataclass
class PreparedPlanning:
    plan: RetrievalPlan | None
    allowed_file_ids: list[str]
    record: dict | None
    scope_failure: DocumentScope | None = None


def prepare_planning(original, resolved, sessions, file_ids, planner: PlannerClient, control: RequestControl) -> PreparedPlanning:
    control.before_answer()
    with sessions() as session:
        ready, scope = resolve_ready_scope(resolved, session, file_ids=file_ids, scope_question=original)
    if not ready:
        return PreparedPlanning(
            direct_plan(original, resolved_question=resolved), [], None,
            scope if scope and scope.status != "resolved" else None,
        )
    generated = planner.plan(original, resolved, control.before_answer)
    control.before_answer()
    return PreparedPlanning(generated.plan, list(ready), generated.record)
