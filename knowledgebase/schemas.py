from pydantic import BaseModel


class Chunk(BaseModel):
    chunk_id: str
    file_id: str
    text: str
    index: int
    start_offset: int
    end_offset: int
