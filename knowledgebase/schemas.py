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
