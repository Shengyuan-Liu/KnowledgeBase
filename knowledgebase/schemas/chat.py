"""Chat requests, responses and saved conversation records."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from .retrieval import EvidenceMetadata, RetrievalDiagnostics


class AnswerSource(EvidenceMetadata):
    """One retrieved excerpt, numbered within the current answer."""

    source_id: int
    file_id: str
    chunk_id: str
    text: str
    start_offset: int | None = None
    end_offset: int | None = None
    start_line: int | None = None
    end_line: int | None = None
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
    retrieval_mode: Literal["single", "planned"] | None = None
    file_ids: list[str] | None = Field(default=None, min_length=1)


class StreamChatRequest(ChatRequest):
    request_id: str = Field(pattern=r"\S")


class ChatStreamEvent(BaseModel):
    """Application event; HTTP framing belongs to the API layer."""

    event: Literal["start", "progress", "sources", "answer_delta", "debug", "complete", "error"]
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
