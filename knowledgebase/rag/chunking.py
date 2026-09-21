from knowledgebase.config import DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP
from knowledgebase.schemas import Chunk


def split_text(
    text: str, file_id: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP
) -> list[Chunk]:
    """Split text into overlapping chunks with end-exclusive character offsets.

    Empty text returns no chunks. IDs combine the file ID and chunk index,
    so reprocessing the same file with the same settings preserves its IDs.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must satisfy 0 <= overlap < chunk_size.")

    start = 0
    chunks: list[Chunk] = []

    while start < len(text):
        end = min(start + chunk_size, len(text))
        index = len(chunks)
        chunks.append(
            Chunk(
                chunk_id=f"{file_id}:{index}",
                file_id=file_id,
                text=text[start:end],
                index=index,
                start_offset=start,
                end_offset=end,
            )
        )
        if end == len(text):
            break
        start = end - overlap

    return chunks
