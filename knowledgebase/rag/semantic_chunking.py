"""Experimental sentence-similarity boundaries inside unchanged structural parents."""

from collections.abc import Callable
from math import sqrt
from time import perf_counter

import tiktoken

from knowledgebase.defaults import (
    DEFAULT_SEMANTIC_BATCH_SIZE,
    DEFAULT_SEMANTIC_SIMILARITY_THRESHOLD,
)
from knowledgebase.rag.chunking import (
    _bounded_units, _pack_units, _sentence_boundaries, _spans_between,
    split_parent_child, split_structured,
)
from knowledgebase.schemas import Chunk, ChunkBatch, SourceBlock


def split_semantic(
    text: str, blocks: list[SourceBlock], file_id: str,
    embed_sentences: Callable[[list[str]], list[list[float]]], *,
    parent_max_tokens: int, child_max_tokens: int, encoding_name: str,
    similarity_threshold: float = DEFAULT_SEMANTIC_SIMILARITY_THRESHOLD,
    batch_size: int = DEFAULT_SEMANTIC_BATCH_SIZE,
) -> tuple[ChunkBatch, dict]:
    """Split prose when adjacent sentence cosine similarity is below the threshold.

    Parents are byte-for-byte identical to the structural parent-child control.
    Each paragraph is a separate group; headings, lists, code and tables keep
    structural splitting. Oversized sentences use the existing bounded-unit
    policy before embedding. Exact source spans reconstruct every scoring input.
    Embeddings only choose boundaries; they never rewrite source text.
    """
    if not -1 <= similarity_threshold <= 1 or batch_size <= 0:
        raise ValueError("Semantic similarity threshold must be in [-1, 1] and batch size positive.")
    hierarchy = split_parent_child(
        text, blocks, file_id, parent_max_tokens=parent_max_tokens,
        child_max_tokens=child_max_tokens, encoding_name=encoding_name,
    )
    encoding = tiktoken.get_encoding(encoding_name)
    groups = []
    inputs = []
    for parent in hierarchy.parents:
        for block_index in parent.source_block_indices:
            block = blocks[block_index]
            start, end = max(parent.start_offset, block.start_offset), min(parent.end_offset, block.end_offset)
            clipped = block.model_copy(update={"text": text[start:end], "start_offset": start, "end_offset": end})
            units = []
            if block.kind == "paragraph":
                boundaries = (start + offset for offset in _sentence_boundaries(text[start:end]))
                for left, right in _spans_between(start, end, boundaries):
                    units.extend(_bounded_units(text, left, right, ("clauses", "words", "characters"), child_max_tokens, encoding))
            input_start = len(inputs)
            if len(units) > 1:
                inputs.extend(units)
            groups.append((parent, block_index, clipped, units, input_start))

    started = perf_counter()
    vectors = []
    for offset in range(0, len(inputs), batch_size):
        batch = inputs[offset:offset + batch_size]
        vectors.extend(embed_sentences([text[start:end] for start, end in batch]))
    embedding_seconds = perf_counter() - started

    children = []
    boundaries = []
    for parent, block_index, block, units, input_start in groups:
        if not units:
            spans = [(c.start_offset, c.end_offset) for c in split_structured(
                text, [block], file_id, max_tokens=child_max_tokens, encoding_name=encoding_name,
            )]
        else:
            sections, section = [], []
            for index, unit in enumerate(units):
                if index:
                    left, right = vectors[input_start + index - 1:input_start + index + 1]
                    similarity = sum(a * b for a, b in zip(left, right, strict=True)) / (
                        sqrt(sum(a * a for a in left)) * sqrt(sum(b * b for b in right))
                    )
                    split = similarity < similarity_threshold
                    boundaries.append({"parent_id": parent.chunk_id, "block_index": block_index,
                        "left_span": list(units[index - 1]), "right_span": list(unit),
                        "cosine_similarity": similarity, "semantic_split": split})
                    if split:
                        sections.append(section)
                        section = []
                section.append(unit)
            sections.append(section)
            spans = [span for section in sections for span in _pack_units(text, section, child_max_tokens, encoding)]
        for start, end in spans:
            children.append(Chunk(type="child",
                chunk_id=f"{file_id}:child:{len(children)}", file_id=file_id,
                text=text[start:end], index=len(children), start_offset=start, end_offset=end,
                parent_id=parent.chunk_id, heading_path=block.heading_path,
                source_block_indices=[block_index], token_count=len(encoding.encode_ordinary(text[start:end])),
                tokenizer=encoding_name, max_tokens=child_max_tokens,
            ))
    diagnostics = {
        "algorithm": "adjacent-sentence-cosine-v1", "sentence_window": 0,
        "similarity_threshold": similarity_threshold, "batch_size": batch_size,
        "input_spans": [list(span) for span in inputs], "boundaries": boundaries,
        "embedding_calls": (len(inputs) + batch_size - 1) // batch_size,
        "embedding_seconds": embedding_seconds,
        "usage": {"status": "unavailable", "value": None,
                  "reason": "The embedding adapter returns vectors only; evaluation call records retain provider usage."},
        "cost": {"status": "unavailable", "value": None, "reason": "Provider billed cost is not exposed."},
    }
    return ChunkBatch(parents=hierarchy.parents, children=children), diagnostics
