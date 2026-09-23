# Structural Chunking

Status: connected to TXT/Markdown uploads using the [document parser](document-parsing.md).
API, CLI, and evaluation entry points share structural chunking settings through
the ingestion service. Existing data is not reindexed automatically.

## Flow and Interface

```text
Original text -> parse_txt / parse_markdown -> SourceBlock list
Original text + SourceBlock list -> split_structured -> StructuredChunk list
```

`split_structured()` in `knowledgebase/rag/chunking.py` receives the original text,
the ordered blocks parsed from that same text, and a file ID. Callers must explicitly
supply `max_tokens` and `encoding_name`. Entry points use the shared
[runtime settings](configuration.md): `CHUNKING_STRATEGY=structural`,
`CHUNK_MAX_TOKENS=512`, and `CHUNK_TOKENIZER=cl100k_base`. This token budget is an
experimental starting point, not a measured optimum. `CHUNKING_STRATEGY=character`
selects the MVP splitter and its character-size/overlap settings explicitly.

```python
from knowledgebase.rag.chunking import split_structured
from knowledgebase.rag.parsing import parse_markdown

source = "# Guide\n\nFirst paragraph.\n\nSecond paragraph.\n"
chunks = split_structured(
    source, parse_markdown(source), "example-file",
    max_tokens=128, encoding_name="cl100k_base",
)

assert len(chunks) == 1
assert chunks[0].heading_path == ["Guide"]
assert chunks[0].source_block_indices == [0, 1, 2]
assert chunks[0].text == source
assert chunks[0].token_count <= 128
```

The example budget is illustrative, not a measured optimum. Token counts apply to
the exact chunk text, including any source markup and separators. Heading metadata
is not prepended to evidence, and no prompt or model-output budget is included.

## Boundary Policy

1. Group adjacent paragraphs under the same heading path. A heading can share a
   group with the following paragraphs. Every new heading begins a new group,
   even when a heading label repeats. Code, tables, lists, blockquotes, reference
   definitions, and thematic breaks each form separate groups.
2. Keep a source block whole when it fits the token budget. Split only oversized
   blocks, using the boundaries below.
3. Greedily pack whole fitting units from each group into chunks. Measure the
   combined original source slice, including blank lines between units, rather
   than adding individual token counts. The resulting chunks have no overlap.

| Oversized content | Preferred boundaries, from coarse to fine |
| --- | --- |
| Paragraph | English sentences, clauses, whitespace-delimited words, characters |
| List | Top-level items with their nested content, lines, words, characters |
| Code, table, blockquote | Lines, words, characters |
| Heading, reference definition, thematic break | Words, characters |

An intact sentence, list item, code line, or table row is kept whenever that unit
fits. A sentence larger than the entire budget must be split further. Clause
boundaries here mean commas, semicolons, or colons followed by whitespace, or a
spaced dash; they are a heuristic, not a grammatical parser.

Only an indivisible oversized unit reaches the final character split. It splits
at Python character boundaries, never at partial UTF-8 bytes. If a character still
cannot fit, the function raises `ValueError` rather than exceeding the budget or
corrupting the source. A positive token limit is required.

Line splitting does not repeat code fences or table headers: such additions would
not be exact original excerpts. Fragments retain their source block associations.
Fitting words are not broken just to include separator whitespace. Whitespace may
remain outside chunk boundaries; all nonblank source content is retained.

## Output and Responsibilities

`StructuredChunk` extends the existing in-memory `Chunk` model. It adds:

- `heading_path`: the section associated with the original blocks.
- `source_block_indices`: zero-based positions in the supplied block list. These
  connect table/code/list fragments back to their original structure.
- `token_count`, `tokenizer`, and `max_tokens`: the measured length and explicit
  counting configuration.

The inherited `text`, `start_offset`, and `end_offset` describe an exact original
source slice. IDs use `<file_id>:structural:<index>` and repeat for the same source
and settings. As with the MVP, changing source or settings requires reindexing;
IDs are not content hashes or cross-configuration identities.

The helpers keep individual responsibilities narrow:

- `_token_count()` measures ordinary document text, including literal spellings
  of special tokens.
- `_sentence_boundaries()` proposes English sentence boundaries. It replaces CR
  and LF with equal-length spaces only for detection, preserving offsets and
  avoiding sentence splits caused solely by source line wraps.
- `_list_boundaries()` identifies top-level item starts using Markdown tokens.
- `_spans_between()` converts boundary positions into contiguous source ranges.
- `_bounded_units()` applies progressively finer boundaries only when necessary.
- `_pack_units()` combines fitting units and remeasures the exact source slice.

Sentence boundaries use [pySBD](https://github.com/nipunsadvilkar/pySBD), with cleaning
disabled and character spans enabled. Token counts use
[tiktoken](https://github.com/openai/tiktoken). Loading an encoding for the first
time may download its public vocabulary into tiktoken's cache. Subsequent calls
use that cache. There are no embedding or generation calls, credentials, or paid
model requests. Sentence detection is heuristic and does not establish semantic
independence or answer quality.

## Verification and Remaining Work

Run `uv run --locked python -m pytest tests/test_structured_chunking.py` for the
new behavior and `make test` for backend regressions. Tests exercise section
boundaries, sentence wraps, abbreviations, decimals, clause/word splitting, nested
lists, code/table boundaries, Unicode, exact token limits, and source preservation
across the frozen DeepSeek Markdown corpus at two budgets.

[Document storage](document-storage.md) can persist the original source, parser
blocks, and structural chunks during ingestion. A separate
[parent-child chunker](parent-child-chunking.md) now builds bounded parents and
children in memory using the same split policy, with
[storage operations](parent-child-storage.md) to retain their relationships.
Ingestion and retrieval integration, overlap, and retrieval-quality comparison remain later work.
`split_structured()` still returns flat chunks used by the active ingestion flow.
