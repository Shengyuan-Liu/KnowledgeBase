from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from knowledgebase.config import RetrievalOptions


class FileInfo(BaseModel):
    file_id: str
    file_name: str
    status: str
    error_message: str | None
    created_at: datetime


class Chunk(BaseModel):
    chunk_id: str
    file_id: str
    text: str
    index: int
    start_offset: int
    end_offset: int


BlockType = Literal[
    "heading", "paragraph", "list", "code", "table", "blockquote",
    "thematic_break", "reference",
]


class SourceBlock(BaseModel):
    """A structural block whose text is an exact slice of the original source."""

    kind: BlockType
    text: str
    start_offset: int
    end_offset: int
    heading_path: list[str]
    heading_level: int | None = None


class StructuredChunk(Chunk):
    """A bounded source slice with its structure and token-counting settings."""

    heading_path: list[str]
    source_block_indices: list[int]
    token_count: int
    tokenizer: str
    max_tokens: int


class ParentChunk(BaseModel):
    """A bounded section region that supplies context for its child chunks."""

    parent_id: str
    file_id: str
    text: str
    index: int
    start_offset: int
    end_offset: int
    heading_path: list[str]
    source_block_indices: list[int]
    token_count: int
    tokenizer: str
    max_tokens: int


class ChildChunk(StructuredChunk):
    """A retrieval-sized source slice contained in exactly one parent."""

    parent_id: str


class ParentChildChunks(BaseModel):
    """Ordered parent and child snapshots, before persistence or indexing."""

    parents: list[ParentChunk]
    children: list[ChildChunk]


class DocumentSource(BaseModel):
    """Canonical document and parser output, independent of a database session."""

    file_id: str
    source_format: Literal["txt", "md"]
    text: str
    source_hash: str
    blocks: list[SourceBlock]


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
    """One fused child with exact text and separately supplied heading context."""

    text: str
    heading_path: list[str] = Field(default_factory=list)


class RelevanceScore(BaseModel):
    """An ordinal relevance assessment, not a correctness probability."""

    chunk_id: str
    score: int = Field(ge=0, le=3, strict=True)


class RerankedMatch(FusedMatch):
    """Original route/fusion metadata plus the independent rerank result."""

    rerank_score: int
    rerank_rank: int


class RerankResult(BaseModel):
    """Full scored input and ranking, including candidates outside selected top-k."""

    question: str
    model: str
    prompt_version: str
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


class RetrievedChunk(BaseModel):
    """Canonical evidence with the highest-ranked child's retrieval provenance."""

    chunk: Chunk
    file_name: str
    distance: float | None
    fusion: FusedMatch | None = None
    parent_id: str | None = None
    matched_child_ids: list[str] = Field(default_factory=list)


class RetrievalCandidate(BaseModel):
    """A selected child/flat hit before parent expansion and evidence packing."""

    chunk_id: str
    distance: float | None
    fusion: FusedMatch | None = None
    file_id: str
    parent_id: str | None = None
    text: str
    start_offset: int
    end_offset: int


class ExcludedEvidence(BaseModel):
    """An entire evidence region skipped because it cannot fit the remaining budget."""

    chunk_id: str
    file_id: str
    token_count: int
    reason: Literal["context_budget"] = "context_budget"


class RetrievalDiagnostics(BaseModel):
    options: RetrievalOptions | None = None
    top_k: int | None = None
    vector_matches: list[VectorMatch] = Field(default_factory=list)
    bm25_matches: list[BM25Match] = Field(default_factory=list)
    fused_matches: list[FusedMatch] = Field(default_factory=list)
    candidates: list[RetrievalCandidate] = Field(default_factory=list)
    excluded: list[ExcludedEvidence] = Field(default_factory=list)
    evidence_tokens: int = 0
    max_tokens: int
    tokenizer: str


class RetrievedEvidence(BaseModel):
    chunks: list[RetrievedChunk]
    diagnostics: RetrievalDiagnostics


class AnswerSource(BaseModel):
    """One retrieved excerpt, numbered within the current answer."""

    source_id: int
    file_id: str
    file_name: str
    chunk_id: str
    text: str
    distance: float | None
    fusion: FusedMatch | None = None
    parent_id: str | None = None
    matched_child_ids: list[str] = Field(default_factory=list)
    start_offset: int | None = None
    end_offset: int | None = None
    heading_path: list[str] = Field(default_factory=list)
    source_block_indices: list[int] = Field(default_factory=list)
    token_count: int | None = None
    tokenizer: str | None = None
    max_tokens: int | None = None


class CitationCheck(BaseModel):
    """Number-to-source matches only; this does not assess factual support."""

    valid_source_ids: list[int]
    invalid_source_ids: list[int]
    no_citations: bool


class ChatAnswer(BaseModel):
    """Answer text and all retrieved sources supplied to the model."""

    answer: str
    sources: list[AnswerSource]
    citation_check: CitationCheck
    retrieval: RetrievalDiagnostics | None = None


class ChatRequest(BaseModel):
    """A nonblank question and an optional saved conversation to continue."""

    question: str = Field(pattern=r"\S")
    conversation_id: str | None = None


class StreamChatRequest(ChatRequest):
    request_id: str = Field(pattern=r"\S")


class ChatStreamEvent(BaseModel):
    """Application event; HTTP framing belongs to the API layer."""

    event: Literal["start", "sources", "answer_delta", "debug", "complete", "error"]
    request_id: str
    data: dict[str, Any]


class ConversationAnswer(ChatAnswer):
    """Completed turn with saved identity and the question used for retrieval."""

    conversation_id: str
    message_id: int
    question: str
    retrieval_question: str


class ConversationInfo(BaseModel):
    """Saved conversation metadata, independent of the database session."""

    conversation_id: str
    created_at: datetime


class MessageInfo(BaseModel):
    """One stored message; history is context, not retrieved evidence."""

    message_id: int
    conversation_id: str
    role: str
    content: str
    created_at: datetime


class HistoricalSource(AnswerSource):
    """A saved excerpt plus the current absence of its original file record."""

    file_deleted: bool


class ConversationMessage(MessageInfo):
    """Display history; null details distinguish unrecorded evidence from none."""

    retrieval_question: str | None = None
    sources: list[HistoricalSource] | None = None
    citation_check: CitationCheck | None = None
    retrieval: RetrievalDiagnostics | None = None


class ConversationDetail(ConversationInfo):
    messages: list[ConversationMessage]
