"""Build budgeted source context with explicit identity and unchanged excerpts."""

import json

from knowledgebase.schemas import RetrievedChunk, StructuredChunk


CONTEXT_FORMAT = "source-metadata-v1"


def build_context(chunks: list[RetrievedChunk]) -> str:
    """Count identity labels as context while preserving canonical source slices."""
    sources = []
    for number, item in enumerate(chunks, start=1):
        metadata = json.dumps({
            "file_name": item.file_name,
            "heading_path": item.chunk.heading_path if isinstance(item.chunk, StructuredChunk) else [],
        }, ensure_ascii=False)
        sources.append(f"[{number}]\nSource metadata: {metadata}\nExcerpt:\n{item.chunk.text}")
    return "\n\n".join(sources)
