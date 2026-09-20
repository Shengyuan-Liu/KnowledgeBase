from datetime import datetime

from pydantic import BaseModel, Field


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


class VectorMatch(BaseModel):
    """A chunk ID and its distance under the collection's configured metric."""

    chunk_id: str
    distance: float


class RetrievedChunk(BaseModel):
    """Canonical chunk text and its vector-search distance."""

    chunk: Chunk
    distance: float


class AnswerSource(BaseModel):
    """One retrieved excerpt, numbered within the current answer."""

    source_id: int
    file_id: str
    file_name: str
    chunk_id: str
    text: str
    distance: float


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


class ChatRequest(BaseModel):
    """A nonblank question and an optional saved conversation to continue."""

    question: str = Field(pattern=r"\S")
    conversation_id: str | None = None


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


class ConversationDetail(ConversationInfo):
    messages: list[ConversationMessage]
