"""Shared search results, ranking provenance and execution traces."""

from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, Field

from knowledgebase.config import RetrievalOptions
from .documents import Chunk, PdfEvidence
from .planning import RetrievalPlan


class VectorMatch(BaseModel):
    """A chunk ID and its distance under the collection's configured metric."""

    chunk_id: str
    distance: float


class BM25Match(BaseModel):
    """A lexical chunk hit: higher scores rank first; ranks start at one."""

    chunk_id: str
    score: float
    rank: int


class FusedMatch(BaseModel):
    """A fused child candidate with separate lexical, vector, and RRF evidence."""

    chunk_id: str
    rrf_score: float
    rank: int
    bm25_score: float | None = None
    bm25_rank: int | None = None
    vector_distance: float | None = None
    vector_rank: int | None = None


class RerankCandidate(FusedMatch):
    """A fused hit scored with its exact child text or an identified whole parent."""

    text: str
    heading_path: list[str] = Field(default_factory=list)
    scoring_parent_id: str | None = None


class RelevanceScore(BaseModel):
    """A raw relevance logit, not a correctness probability."""

    chunk_id: str
    score: float = Field(allow_inf_nan=False)


class RerankedMatch(FusedMatch):
    """Original route/fusion metadata plus the independent rerank result."""

    rerank_score: float
    rerank_rank: int
    score_kind: str = "ordinal_0_3"
    scoring_parent_id: str | None = None


class RerankResult(BaseModel):
    """Full scored input and ranking, including candidates outside selected top-k."""

    question: str
    model: str
    prompt_version: str
    score_kind: str = "ordinal_0_3"
    model_revision: str | None = None
    device: str | None = None
    max_pair_tokens: int | None = None
    batch_size: int | None = None
    tokenizer: str
    input_tokens: int
    candidate_limit: int
    max_input_tokens: int
    top_k: int
    candidates: list[RerankCandidate]
    matches: list[RerankedMatch]

    @property
    def selected(self) -> list[RerankedMatch]:
        return self.matches[:self.top_k]


class RetrievalMetadata(BaseModel):
    """Ranking provenance shared by candidates and supplied sources."""

    distance: float | None
    fusion: FusedMatch | None = None
    rerank: RerankedMatch | None = None
    parent_id: str | None = None


class EvidenceMetadata(RetrievalMetadata):
    """Source metadata retained both during retrieval and in answer snapshots."""

    pdf: PdfEvidence | None = None
    document_labels: list[str] = Field(default_factory=list)
    file_name: str
    matched_child_ids: list[str] = Field(default_factory=list)


class RetrievedChunk(EvidenceMetadata):
    """Canonical evidence with the highest-ranked child's retrieval provenance."""

    chunk: Chunk


class RetrievalCandidate(RetrievalMetadata):
    """A selected child/flat hit before parent expansion and evidence packing."""

    chunk_id: str
    file_id: str
    text: str
    start_offset: int
    end_offset: int


class ExcludedEvidence(BaseModel):
    """An omitted region; trial cost includes the other sources in that attempt."""

    chunk_id: str
    file_id: str
    token_count: int
    trial_context_tokens: int | None = None
    reason: Literal["context_budget"] = "context_budget"


class ScopeFile(BaseModel):
    """A file identity used to resolve a document reference."""

    file_id: str
    file_name: str
    labels: list[str] = Field(default_factory=list)


class DocumentScope(BaseModel):
    status: Literal["resolved", "ambiguous", "not_found"]
    references: list[str] = Field(default_factory=list)
    file_ids: list[str] = Field(default_factory=list)
    matches: list[ScopeFile] = Field(default_factory=list)
    message: str | None = None


class RetrievalDiagnostics(BaseModel):
    planning: dict[str, Any] | None = None
    document_scope: DocumentScope | None = None
    scope_seconds: float | None = None
    retrieval_seconds: float | None = None
    embedding_seconds: float | None = None
    rerank: RerankResult | None = None
    rerank_seconds: float | None = None
    options: RetrievalOptions | None = None
    top_k: int | None = None
    vector_matches: list[VectorMatch] = Field(default_factory=list)
    bm25_matches: list[BM25Match] = Field(default_factory=list)
    fused_matches: list[FusedMatch] = Field(default_factory=list)
    candidates: list[RetrievalCandidate] = Field(default_factory=list)
    excluded: list[ExcludedEvidence] = Field(default_factory=list)
    unexpanded_parents: list[ExcludedEvidence] = Field(default_factory=list)
    packing_seconds: float | None = None
    context_format: str | None = None
    evidence_tokens: int = 0
    max_tokens: int
    tokenizer: str


class RetrievedEvidence(BaseModel):
    """Search or packed results; diagnostics identify the completed stages.

    Read the old query-run field `hits` when restoring v1 planning traces.
    New results consistently serialize as `chunks`.
    """

    chunks: list[RetrievedChunk] = Field(validation_alias=AliasChoices("chunks", "hits"))
    diagnostics: RetrievalDiagnostics


class QueryRun(BaseModel):
    round_index: int = 1
    query_ids: list[str]
    requirement_ids: list[str]
    text: str
    requested_file_ids: list[str] | None
    result: RetrievedEvidence
    seconds: float


class QueryVote(BaseModel):
    run_index: int
    rank: int


class MergedCandidate(BaseModel):
    chunk_id: str
    file_id: str
    score: float
    rank: int
    votes: list[QueryVote]


class RequirementEvidence(BaseModel):
    """Retrieval attribution only; a hit does not prove semantic support."""
    requirement_id: str
    candidate_ids: list[str]
    selected_ids: list[str]
    supplied_ids: list[str]
    budget_excluded_ids: list[str]


class PlanTrace(BaseModel):
    version: Literal[1, 2] = 2
    plan: RetrievalPlan
    allowed_file_ids: list[str]
    document_scope: DocumentScope | None
    cross_query_rrf_k: float
    per_query_limit: int
    top_k: int
    max_evidence_tokens: int
    runs: list[QueryRun] = Field(default_factory=list)
    merged: list[MergedCandidate] = Field(default_factory=list)
    selected_ids: list[str] = Field(default_factory=list)
    requirements: list[RequirementEvidence] = Field(default_factory=list)
    stop_reason: Literal["independent_queries_complete", "scope_unresolved", "no_ready_files"]
    scope_seconds: float = 0
    merge_seconds: float = 0
    total_seconds: float = 0


class PlannedEvidence(BaseModel):
    evidence: RetrievedEvidence
    trace: PlanTrace
