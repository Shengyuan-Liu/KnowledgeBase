# Document Parsing

Status: connected to TXT/Markdown uploads through the shared ingestion service.
Both chunking strategies retain parser blocks alongside the complete source;
structural chunking also uses the block boundaries to produce chunks.

## Role and Interface

`knowledgebase/rag/parsing.py` identifies source structure before chunking:

- `parse_txt(text)` groups consecutive nonblank lines into paragraph blocks.
  Markdown-looking text remains ordinary text.
- `parse_markdown(text)` identifies headings, paragraphs, lists, code, tables,
  blockquotes, thematic breaks, and link-reference definitions.
- `_line_offsets(text)` maps line boundaries to positions in the original string.
  It recognizes LF, CRLF, and CR without changing the source.

Both public functions accept decoded text and return an ordered `list[SourceBlock]`.
They perform no file, database, network, embedding, or model operations. Empty and
blank-only input returns an empty list; upload validation remains a service concern.

`SourceBlock` in `knowledgebase/schemas.py` is an in-memory Pydantic data model,
not a database table, stored chunk, or HTTP response contract.

| Field | Meaning |
| --- | --- |
| `kind` | Structural category, such as `heading`, `paragraph`, `code`, or `table` |
| `text` | Exact original source slice, including source markup and line endings |
| `start_offset`, `end_offset` | Zero-based, end-exclusive Python character offsets |
| `heading_path` | Active outer-to-inner heading labels; a heading includes itself |
| `heading_level` | Heading depth from 1 to 6; `None` for other blocks |

Every block satisfies `block.text == text[block.start_offset:block.end_offset]`.
Offsets count Unicode characters, not UTF-8 bytes. Blocks do not overlap. Blank
separators may be outside blocks and remain available in the original source.
Consumers must retain that source rather than reconstruct it by joining blocks.

## Markdown Interpretation

The implementation uses
[markdown-it-py](https://markdown-it-py.readthedocs.io/en/latest/using.html)
with CommonMark rules, the table rule enabled, and HTML parsing disabled. It reads
block line maps, then slices the original input instead of using normalized token
content as evidence. Parsing never renders HTML or fetches linked resources.

- ATX (`# Title`) and Setext (underlined) headings update the heading path.
  A new heading replaces the previous heading at the same or deeper level.
  Skipped levels do not create synthetic headings.
- Heading labels omit the outer heading markers but retain inline Markdown such
  as emphasis and backticks. Labels are metadata, separate from quoted evidence.
- Lists and blockquotes are whole top-level regions. Nested paragraphs, lists,
  headings, and code remain inside that region rather than producing overlapping
  blocks. A heading inside a quote or list does not change the document's path.
- Fenced and indented code become `code` blocks. Fence markers and indentation
  remain in source text. Pipe tables remain whole `table` blocks.
- Link-reference definitions remain explicit `reference` blocks, including
  repeated definitions. Links and images stay in their original Markdown form.

This is CommonMark plus pipe tables, not an MDX or full GitHub Markdown parser.
There is no front-matter interpretation, token budget, sentence splitting,
parent-child hierarchy, or database persistence in this step. Long structures
remain intact for the [structural chunker](structural-chunking.md) to handle.

## Example

```python
from knowledgebase.rag.parsing import parse_markdown

source = "# Guide\n\n## Setup\n\nInstall the package.\n"
blocks = parse_markdown(source)

assert blocks[-1].kind == "paragraph"
assert blocks[-1].heading_path == ["Guide", "Setup"]
assert blocks[-1].text == "Install the package.\n"
assert blocks[-1].text == source[blocks[-1].start_offset:blocks[-1].end_offset]
```

## Verification

Run `uv run --locked python -m pytest tests/test_parsing.py` for parsing tests and
`make test` for the backend regression suite. Tests cover structure, heading
scope, original newlines, Unicode positions, code, tables, nested containers,
reference definitions, and source-span coverage across the frozen DeepSeek corpus.
Corpus coverage checks preservation of source content, not retrieval quality.
