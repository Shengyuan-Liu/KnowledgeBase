import re
from collections.abc import Iterable, Iterator

import pysbd
import tiktoken
from markdown_it import MarkdownIt

from knowledgebase.config import DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP
from knowledgebase.schemas import Chunk, SourceBlock, StructuredChunk


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


def split_structured(
    text: str, blocks: list[SourceBlock], file_id: str, *,
    max_tokens: int, encoding_name: str,
) -> list[StructuredChunk]:
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

    chunks: list[StructuredChunk] = []
    for group in groups:
        units: list[tuple[int, int]] = []
        for block_index in group:
            block = blocks[block_index]
            if block.kind == "paragraph":
                stages = ("sentences", "clauses", "words", "characters")
            elif block.kind == "list":
                stages = ("items", "lines", "words", "characters")
            elif block.kind in ("code", "table", "blockquote"):
                stages = ("lines", "words", "characters")
            else:
                stages = ("words", "characters")
            units.extend(_bounded_units(
                text, block.start_offset, block.end_offset, stages, max_tokens, encoding,
            ))
        for start, end in _pack_units(text, units, max_tokens, encoding):
            excerpt = text[start:end]
            index = len(chunks)
            chunks.append(StructuredChunk(
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
