from datetime import datetime

from pydantic import BaseModel


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


class ChatAnswer(BaseModel):
    """Answer text and all retrieved sources supplied to the model."""

    answer: str
    sources: list[AnswerSource]


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
