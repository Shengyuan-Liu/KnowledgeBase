# Parent-Child Chunking

Status: implemented as a standalone v1 function with in-memory data models.
The active upload and retrieval workflow still uses flat structural chunks.
[Parent-child storage](parent-child-storage.md) now persists this output;
ingestion integration, indexing, and retrieval expansion are later steps.

## Interface and Models

`split_parent_child()` in `knowledgebase/rag/chunking.py` takes the complete decoded
source, its ordered `SourceBlock` list, a file ID, and explicit parent/child token
limits plus a tokenizer name. It returns `ParentChildChunks`:

| Model in `knowledgebase/schemas.py` | Role |
| --- | --- |
| `ParentChunk` | Bounded section context, identified by `parent_id` |
| `ChildChunk` | Extends `StructuredChunk` with the ID of its one enclosing parent |
| `ParentChildChunks` | Contains ordered `parents` and `children` lists |

Parents and children both retain file ID, exact text, document-global index,
half-open source offsets, heading path, source block indices, measured token count,
tokenizer, and their own token limit. Offsets count Python Unicode characters, not
UTF-8 bytes. Block indices refer to the original input list, not a list local to a
parent. Parent and child indices each start at zero and increase across the file.

These are Pydantic snapshots, not database tables or new HTTP response contracts.
`save_parent_child_chunks()` persists these snapshots and their relationships;
`save_chunks()` can also save children when their parents already exist.

## Boundary Policy

1. Start a new section at every heading, including repeated labels and nested
   headings. Content before the first heading forms its own section. Different
   heading paths also separate sections. TXT paragraphs share one section because
   their heading paths are empty.
2. Within a section, greedily pack original blocks into bounded parents. A parent
   may include prose, lists, code, and tables from that same section. A fitting
   block stays whole; only an oversized block uses the existing structural
   sentence/item/line splitting policy. The exact combined source slice, including
   separators, must fit the parent budget.
3. Intersect the original blocks with each parent range. Preserve each intersected
   block's kind and heading path; do not reparse a code or list fragment as a new
   Markdown document.
4. Run structural child splitting inside those clipped blocks, using the separate
   child budget. Prose may share a child with its heading; lists, code, tables,
   and other block types retain the existing separate-group policy. Map the child
   block indices back to the original document and attach its `parent_id`.

Every child lies entirely within exactly one parent and has the same heading path.
Parents do not overlap one another; children do not overlap one another. A parent
can contain a single child, including when both text slices are identical. They
need not reach their size limits. Short headings can form small parents or children.

Neither level synthesizes heading prefixes, repeats code fences/table headers, or
normalizes source whitespace. Blank separators may remain outside region boundaries;
all nonblank source content remains covered. Oversized sentences prefer clauses,
then words; oversized code/table blocks prefer lines. An indivisible unit exceeding
the hard budget can require character splitting, as described in the
[structural boundary policy](structural-chunking.md#boundary-policy).

Both limits must be positive, and `child_max_tokens` cannot exceed
`parent_max_tokens`. Equal limits are permitted. This step introduces no runtime
defaults or `.env` options: callers choose explicit experimental budgets.

## Example

```python
from knowledgebase.rag.chunking import split_parent_child
from knowledgebase.rag.parsing import parse_markdown

text = "# Guide\n\nInstall the package.\n\n- Restart the server.\n"
result = split_parent_child(
    text, parse_markdown(text), "guide-1",
    parent_max_tokens=64, child_max_tokens=16, encoding_name="cl100k_base",
)

assert len(result.parents) == 1
assert len(result.children) == 2
parent = result.parents[0]
assert parent.text == text
for child in result.children:
    assert child.parent_id == parent.parent_id
    assert parent.start_offset <= child.start_offset < child.end_offset <= parent.end_offset
    assert child.text == text[child.start_offset:child.end_offset]
```

The parent retains both the installation paragraph and restart list. Its children
keep the prose and list as separate retrieval units. Retrieval expansion is not
implemented by this function; it will later load the parent for a selected child.

Parent IDs use `<file_id>:parent:<index>` and child IDs use
`<file_id>:child:<index>`. The same inputs and settings produce the same IDs and
output. These are ordered identities, not content hashes: changed settings or
source require reindexing rather than reusing an old relationship map.

## Verification

Run `uv run --locked python -m pytest tests/test_parent_child_chunking.py` for this
step and `make test` for backend regressions. Tests cover mixed-block context,
repeated/nested headings, oversized sections, sentence/line boundaries, exact
Unicode and CRLF slices, separate token limits, global source-block associations,
stable IDs, serialization, and unique parent containment. The frozen DeepSeek
Markdown corpus is checked at parent/child budgets of 64/16 and 256/64 tokens.

The shared `_block_units()` helper applies the existing split policy at both
levels; existing flat structural tests protect its behavior. No embeddings,
generation requests, storage mutations, or credentials are involved. A tokenizer
may download its public vocabulary on first use. These checks establish chunking
invariants, not improved retrieval or answer quality.
