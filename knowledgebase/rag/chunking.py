from dataclasses import dataclass
import re
from collections.abc import Iterable, Iterator

import pysbd
import tiktoken
from markdown_it import MarkdownIt

from knowledgebase.config import DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP
from knowledgebase.schemas import (
    Chunk, ChunkBatch, SourceBlock,
)

from knowledgebase.config import (
    DEFAULT_CHUNKING_STRATEGY, DEFAULT_CHUNK_MAX_TOKENS, DEFAULT_CHUNK_TOKENIZER,
    DEFAULT_PARENT_MAX_TOKENS, DEFAULT_SEMANTIC_SIMILARITY_THRESHOLD, DEFAULT_SEMANTIC_BATCH_SIZE,
)
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.rag.pdf_evidence import table_rows
from knowledgebase.rag.pdf_chunking import PDF_PARENT_CONTEXT_VERSION, join_heading_parents
from knowledgebase.schemas import File


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


def _token_count(text: str, encoding: tiktoken.Encoding) -> int:
    """Count all source content as ordinary text, including special-token spellings."""
    return len(encoding.encode_ordinary(text))


def _spans_between(start: int, end: int, boundaries: Iterable[int]) -> Iterator[tuple[int, int]]:
    """Partition one source interval at ordered interior boundaries."""
    for boundary in boundaries:
        if start < boundary < end:
            yield start, boundary
            start = boundary
    if start < end:
        yield start, end


def _sentence_boundaries(text: str) -> list[int]:
    """Detect English sentences without treating source line wraps as sentence ends."""
    detection_text = re.sub(r"[\r\n]", " ", text)
    sentences = pysbd.Segmenter(language="en", clean=False, char_span=True).segment(detection_text)
    return [sentence.start for sentence in sentences[1:]]


def _list_boundaries(text: str) -> list[int]:
    """Find top-level list item starts; nested content stays with its item."""
    offsets = [0, *(match.end() for match in re.finditer(r"\r\n|\r|\n", text)), len(text)]
    return [
        offsets[token.map[0]]
        for token in MarkdownIt("commonmark").parse(text)
        if token.type == "list_item_open" and token.level == 1
    ]


def _bounded_units(
    text: str, start: int, end: int, stages: tuple[str, ...],
    max_tokens: int, encoding: tiktoken.Encoding,
) -> Iterator[tuple[int, int]]:
    """Split only oversized units, preferring structure before finer boundaries."""
    excerpt = text[start:end]
    if _token_count(excerpt, encoding) <= max_tokens:
        yield start, end
        return

    if not stages:
        # The final indivisible unit is one Python character, never a partial UTF-8 byte.
        raise ValueError("max_tokens is too small to retain one source character.")

    stage, *remaining = stages
    if stage == "sentences":
        boundaries = _sentence_boundaries(excerpt)
    elif stage == "items":
        boundaries = _list_boundaries(excerpt)
    elif stage == "lines":
        boundaries = [match.end() for match in re.finditer(r"\r\n|\r|\n", excerpt)]
    elif stage == "clauses":
        boundaries = [match.end() for match in re.finditer(r"[,;:]\s+|\s+[—–]\s+", excerpt)]
    elif stage == "words":
        # Keep a fitting word whole even when surrounding whitespace exceeds the budget.
        # Packing recovers separators from the source whenever words share a chunk.
        for word in re.finditer(r"\S+", excerpt):
            yield from _bounded_units(
                text, start + word.start(), start + word.end(), tuple(remaining),
                max_tokens, encoding,
            )
        return
    else:
        boundaries = range(1, len(excerpt))

    for unit_start, unit_end in _spans_between(start, end, (start + b for b in boundaries)):
        yield from _bounded_units(
            text, unit_start, unit_end, tuple(remaining), max_tokens, encoding,
        )


def _pack_units(
    text: str, units: Iterable[tuple[int, int]], max_tokens: int, encoding: tiktoken.Encoding,
) -> Iterator[tuple[int, int]]:
    """Greedily combine whole units, counting the exact slice including separators."""
    start: int | None = None
    end = 0
    for unit_start, unit_end in units:
        if start is not None and _token_count(text[start:unit_end], encoding) > max_tokens:
            yield start, end
            start = None
        if start is None:
            start = unit_start
        end = unit_end
    if start is not None:
        yield start, end


def _block_units(
    text: str, block: SourceBlock, max_tokens: int, encoding: tiktoken.Encoding,
    row_spans: list[tuple[int, int]] | None = None,
) -> Iterator[tuple[int, int]]:
    """Apply the same structure-specific split policy at either chunking level."""
    if row_spans is not None and _token_count(block.text, encoding) > max_tokens:
        for row_start, row_end in row_spans:
            start, end = max(block.start_offset, row_start), min(block.end_offset, row_end)
            if start < end:
                yield from _bounded_units(text, start, end, ("words", "characters"), max_tokens, encoding)
        return
    if block.kind == "paragraph":
        stages = ("sentences", "clauses", "words", "characters")
    elif block.kind == "list":
        stages = ("items", "lines", "words", "characters")
    elif block.kind in ("code", "table", "blockquote"):
        stages = ("lines", "words", "characters")
    else:
        stages = ("words", "characters")
    yield from _bounded_units(
        text, block.start_offset, block.end_offset, stages, max_tokens, encoding,
    )


def split_structured(
    text: str, blocks: list[SourceBlock], file_id: str, *,
    max_tokens: int, encoding_name: str,
    table_row_spans: dict[int, list[tuple[int, int]]] | None = None,
) -> list[Chunk]:
    """Build nonoverlapping chunks from this source's ordered parser output.

    Adjacent paragraphs can share a chunk with their section heading. Each new
    heading starts a new group, even if its label repeats. Other block types stay
    separate. Oversized prose splits at sentences, clauses, then words; code and
    tables split at lines. An oversized indivisible unit finally splits at Python
    character boundaries. Original text, offsets, and block associations survive.

    Limits and tokenizer are explicit experimental settings, not MVP defaults.
    No storage, embeddings, or model requests are involved. Loading a tokenizer
    may download its public vocabulary on first use through tiktoken's cache.
    """
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive.")
    encoding = tiktoken.get_encoding(encoding_name)

    groups: list[list[int]] = []
    for index, block in enumerate(blocks):
        if (
            groups and block.kind == "paragraph"
            and blocks[index - 1].kind in ("heading", "paragraph")
            and blocks[index - 1].heading_path == block.heading_path
        ):
            groups[-1].append(index)
        else:
            groups.append([index])

    chunks: list[Chunk] = []
    for group in groups:
        units: list[tuple[int, int]] = []
        for block_index in group:
            units.extend(_block_units(text, blocks[block_index], max_tokens, encoding,
                                      (table_row_spans or {}).get(block_index)))
        for start, end in _pack_units(text, units, max_tokens, encoding):
            excerpt = text[start:end]
            index = len(chunks)
            chunks.append(Chunk(
                chunk_id=f"{file_id}:structural:{index}", file_id=file_id,
                text=excerpt, index=index, start_offset=start, end_offset=end,
                heading_path=blocks[group[0]].heading_path,
                source_block_indices=[
                    i for i in group
                    if blocks[i].start_offset < end and blocks[i].end_offset > start
                ],
                token_count=_token_count(excerpt, encoding),
                tokenizer=encoding.name, max_tokens=max_tokens,
            ))
    return chunks


def split_parent_child(
    text: str, blocks: list[SourceBlock], file_id: str, *,
    parent_max_tokens: int, child_max_tokens: int, encoding_name: str,
    table_row_spans: dict[int, list[tuple[int, int]]] | None = None,
) -> ChunkBatch:
    """Build bounded section parents, then structural children within each parent.

    Every heading starts a section, including repeated labels and nested headings.
    Within a section, parents can combine different block types. Both levels keep
    exact original slices and global source-block indices without overlap. This
    function does not persist records or change the active ingestion strategy.
    """
    if parent_max_tokens <= 0 or child_max_tokens <= 0:
        raise ValueError("parent_max_tokens and child_max_tokens must be positive.")
    if child_max_tokens > parent_max_tokens:
        raise ValueError("child_max_tokens must not exceed parent_max_tokens.")
    encoding = tiktoken.get_encoding(encoding_name)

    sections: list[list[int]] = []
    for index, block in enumerate(blocks):
        if (
            not sections or block.kind == "heading"
            or block.heading_path != blocks[sections[-1][0]].heading_path
        ):
            sections.append([])
        sections[-1].append(index)

    parents: list[Chunk] = []
    children: list[Chunk] = []
    for section in sections:
        units = (
            span for i in section
            for span in _block_units(text, blocks[i], parent_max_tokens, encoding,
                                     (table_row_spans or {}).get(i))
        )
        for start, end in _pack_units(text, units, parent_max_tokens, encoding):
            parent = Chunk(type="parent",
                chunk_id=f"{file_id}:parent:{len(parents)}", file_id=file_id,
                text=text[start:end], index=len(parents), start_offset=start, end_offset=end,
                heading_path=blocks[section[0]].heading_path,
                source_block_indices=[
                    i for i in section if blocks[i].start_offset < end and blocks[i].end_offset > start
                ],
                token_count=_token_count(text[start:end], encoding),
                tokenizer=encoding.name, max_tokens=parent_max_tokens,
            )
            parents.append(parent)
            # Clip existing blocks, preserving their kinds and original heading paths.
            # Reparsing a code/list fragment could reinterpret its Markdown structure.
            clipped: list[SourceBlock] = []
            for i in parent.source_block_indices:
                block = blocks[i]
                block_start, block_end = max(start, block.start_offset), min(end, block.end_offset)
                clipped.append(block.model_copy(update={
                    "text": text[block_start:block_end],
                    "start_offset": block_start, "end_offset": block_end,
                }))
            for chunk in split_structured(
                text, clipped, file_id, max_tokens=child_max_tokens, encoding_name=encoding_name,
                table_row_spans={local: table_row_spans[original]
                                 for local, original in enumerate(parent.source_block_indices)
                                 if table_row_spans and original in table_row_spans},
            ):
                children.append(Chunk(**{
                    **chunk.model_dump(),
                    "type": "child",
                    "chunk_id": f"{file_id}:child:{len(children)}", "index": len(children),
                    "parent_id": parent.chunk_id,
                    "source_block_indices": [parent.source_block_indices[i] for i in chunk.source_block_indices],
                }))
    return ChunkBatch(parents=parents, children=children)


@dataclass
class DocumentChunker:
    """Own indexing settings and dispatch to the source-preserving split algorithms."""

    chunk_size: int = DEFAULT_CHUNK_SIZE
    overlap: int = DEFAULT_OVERLAP
    chunking_strategy: str = DEFAULT_CHUNKING_STRATEGY
    chunk_max_tokens: int = DEFAULT_CHUNK_MAX_TOKENS
    chunk_tokenizer: str = DEFAULT_CHUNK_TOKENIZER
    parent_max_tokens: int = DEFAULT_PARENT_MAX_TOKENS
    semantic_similarity_threshold: float = DEFAULT_SEMANTIC_SIMILARITY_THRESHOLD
    semantic_batch_size: int = DEFAULT_SEMANTIC_BATCH_SIZE
    embedding_model: str | None = None

    embeddings: EmbeddingClient | None = None

    def split(self, file: File) -> tuple[ChunkBatch, dict]:
        strategy = "parent_child" if file.type == "pdf" else self.chunking_strategy
        semantic = None
        if strategy == "semantic":
            from knowledgebase.rag.semantic_chunking import split_semantic

            batch, semantic = split_semantic(
                file.text, file.blocks, file.file_id, self.embeddings.embed_documents,
                parent_max_tokens=self.parent_max_tokens, child_max_tokens=self.chunk_max_tokens,
                encoding_name=self.chunk_tokenizer, similarity_threshold=self.semantic_similarity_threshold,
                batch_size=self.semantic_batch_size,
            )
        elif strategy == "parent_child":
            batch = split_parent_child(
                file.text, file.blocks, file.file_id, parent_max_tokens=self.parent_max_tokens,
                child_max_tokens=self.chunk_max_tokens, encoding_name=self.chunk_tokenizer,
                table_row_spans=table_rows(file) if file.type == "pdf" else None,
            )
            if file.type == "pdf":
                batch = join_heading_parents(file, batch)
        elif strategy == "structural":
            batch = ChunkBatch([], split_structured(
                file.text, file.blocks, file.file_id, max_tokens=self.chunk_max_tokens,
                encoding_name=self.chunk_tokenizer,
            ))
        elif strategy == "character":
            batch = ChunkBatch([], split_text(file.text, file.file_id, self.chunk_size, self.overlap))
        else:
            raise ValueError("chunking_strategy must be structural, character, parent_child, or semantic.")
        indexing = {
            "strategy": strategy, "embedding_model": self.embedding_model,
            "chunk_max_tokens": self.chunk_max_tokens, "parent_max_tokens": self.parent_max_tokens,
            "tokenizer": self.chunk_tokenizer, "chunk_size": self.chunk_size, "overlap": self.overlap,
            "semantic": semantic,
        }
        if file.type == "pdf":
            indexing["pdf_parent_context"] = PDF_PARENT_CONTEXT_VERSION
        return batch, indexing
