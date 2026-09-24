"""Build numbered source context from retrieved chunks."""

from knowledgebase.schemas import RetrievedChunk


def build_context(chunks: list[RetrievedChunk]) -> str:
    """Preserve retrieval order and source text; source [n] is chunks[n - 1]."""
    return "\n\n".join(
        f"[{number}]\n{item.chunk.text}"
        for number, item in enumerate(chunks, start=1)
    )
