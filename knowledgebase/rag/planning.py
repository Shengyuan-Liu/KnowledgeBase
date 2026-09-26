"""Typed, bounded plans supplied by callers; no model calls or response repair."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PlanRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AnswerRequirement(PlanRecord):
    requirement_id: str = Field(min_length=1)
    description: str = Field(min_length=1)


class PlannedQuery(PlanRecord):
    query_id: str = Field(min_length=1)
    text: str = Field(min_length=1, pattern=r"\S")
    requirement_ids: list[str] = Field(min_length=1)
    # None inherits the user's scope. An explicit list can only narrow it.
    file_ids: list[str] | None = None


class RetrievalPlan(PlanRecord):
    original_question: str = Field(min_length=1)
    resolved_question: str = Field(min_length=1)
    route: Literal["direct", "decomposed"]
    requirements: list[AnswerRequirement] = Field(min_length=1, max_length=6)
    queries: list[PlannedQuery] = Field(min_length=1, max_length=6)

    @model_validator(mode="after")
    def consistent_references(self) -> Self:
        requirements = {item.requirement_id for item in self.requirements}
        if len(requirements) != len(self.requirements):
            raise ValueError("Requirement IDs must be unique.")
        if len({query.query_id for query in self.queries}) != len(self.queries):
            raise ValueError("Query IDs must be unique.")
        addressed = {identity for query in self.queries for identity in query.requirement_ids}
        if addressed != requirements:
            raise ValueError("Queries must reference known requirements and address every requirement.")
        if self.route == "direct" and (len(self.queries) != 1 or self.queries[0].text != self.resolved_question):
            raise ValueError("A direct plan must query the resolved question exactly once.")
        return self


def direct_plan(question: str, *, resolved_question: str | None = None) -> RetrievalPlan:
    """Construct the existing single-query route without a planner/model call."""
    resolved = resolved_question if resolved_question is not None else question
    return RetrievalPlan(
        original_question=question, resolved_question=resolved, route="direct",
        requirements=[AnswerRequirement(requirement_id="answer", description=question)],
        queries=[PlannedQuery(query_id="direct", text=resolved, requirement_ids=["answer"])],
    )
