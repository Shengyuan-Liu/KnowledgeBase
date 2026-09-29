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


class DependentQuery(PlanRecord):
    query_id: str = Field(min_length=1)
    query_template: str = Field(
        min_length=1, pattern=r"\{target\}",
        description="Search with exactly one literal {target} for an entity or term not yet known, to be extracted from prerequisite evidence.",
    )
    requirement_ids: list[str] = Field(min_length=1)
    depends_on: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def one_target(self) -> Self:
        if self.query_template.count("{target}") != 1:
            raise ValueError("A dependent query needs exactly one {target} placeholder.")
        return self


class RetrievalPlan(PlanRecord):
    original_question: str = Field(min_length=1)
    resolved_question: str = Field(min_length=1)
    route: Literal["direct", "decomposed", "dependent"]
    requirements: list[AnswerRequirement] = Field(min_length=1, max_length=6)
    queries: list[PlannedQuery] = Field(min_length=1, max_length=6)
    dependencies: list[DependentQuery] = Field(default_factory=list, max_length=5)
    # Answer behavior is retained for traceability, not scored as source evidence.
    answer_rules: list[str] = Field(default_factory=list, max_length=6)

    @model_validator(mode="after")
    def consistent_references(self) -> Self:
        requirements = {item.requirement_id for item in self.requirements}
        if len(requirements) != len(self.requirements):
            raise ValueError("Requirement IDs must be unique.")
        nodes = [*self.queries, *self.dependencies]
        if len(nodes) > 6:
            raise ValueError("A plan permits at most six queries including dependencies.")
        if len({query.query_id for query in nodes}) != len(nodes):
            raise ValueError("Query IDs must be unique.")
        depths = {query.query_id: 1 for query in self.queries}
        for dependency in self.dependencies:
            if not set(dependency.depends_on) <= depths.keys():
                raise ValueError("Dependencies must reference earlier queries in topological order.")
            depths[dependency.query_id] = 1 + max(depths[parent] for parent in dependency.depends_on)
        if max(depths.values()) > 3:
            raise ValueError("A dependency chain permits at most three retrieval rounds.")
        if bool(self.dependencies) != (self.route == "dependent"):
            raise ValueError("Only dependent plans may contain pending queries.")
        addressed = {identity for query in nodes for identity in query.requirement_ids}
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


class DraftQuery(PlanRecord):
    query_id: str = Field(min_length=1)
    text: str = Field(pattern=r"\S")
    requirement_ids: list[str] = Field(min_length=1)


class PlanDecision(PlanRecord):
    """Model output cannot replace questions or authorize file identities."""
    route: Literal["direct", "decomposed", "dependent", "needs_narrowing"]
    requirements: list[AnswerRequirement] = Field(max_length=6)
    queries: list[DraftQuery] = Field(max_length=6)
    dependencies: list[DependentQuery] = Field(max_length=5)
    answer_rules: list[str] = Field(
        default_factory=list, max_length=6,
        description="Exact original-question quotes specifying how to present the answer or disclose evidence limits. Exclude factual questions and their conditions, even when quoted exactly. Empty when there is no separate answering instruction.",
    )

    def to_plan(self, original: str, resolved: str) -> RetrievalPlan | None:
        if self.route in {"direct", "needs_narrowing"}:
            if self.requirements or self.queries or self.dependencies:
                raise ValueError("Direct and narrowing decisions must have empty requirement/query lists.")
            return (direct_plan(original, resolved_question=resolved).model_copy(update={"answer_rules": self.answer_rules})
                    if self.route == "direct" else None)
        return RetrievalPlan(
            original_question=original, resolved_question=resolved, route=self.route,
            requirements=self.requirements,
            queries=[PlannedQuery(**query.model_dump()) for query in self.queries],
            dependencies=self.dependencies,
            answer_rules=self.answer_rules,
        )
