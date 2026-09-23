# Parent-Child Storage

Status: implemented and tested as storage operations. The
[parent-child splitter](parent-child-chunking.md) can persist its output and read
it back with complete relationships. [Parent-child retrieval](parent-child-retrieval.md)
connects these operations to ingestion and evidence expansion when new uploads
use the default `parent_child` strategy.

## Tables and Responsibilities

Existing table columns are unchanged. `init_db()` adds two tables:

| Table and ORM model | Role |
| --- | --- |
| `parent_chunks` / `ParentChunkRecord` | Store each parent's ID, file ID, source order, exact text and offsets, heading path, source block indices, token count, tokenizer, and token limit |
| `child_parents` / `ChildParentRecord` | Associate one structural child `chunk_id` with one `parent_id` |

Children reuse `chunks` for original text/offsets and `chunk_structures` for their
structural metadata. Parent text is stored separately; it does not become an
indexed child or appear in `get_chunks()` results. The existing
[document source](document-storage.md) retains the complete source and parser blocks.

A parent references an existing file and has a unique `(file_id, index)` pair.
A child link's primary key is `chunk_id`, so a child cannot have two parent links.
Its foreign keys require an existing structural chunk and an existing parent.
Deleting a referenced parent alone fails rather than silently removing the link.

The splitter owns the same-file, source containment, and exact-text invariants.
Storage callers supply its output from the same canonical source; the storage
layer does not recompute token counts, reparse Markdown, or validate those
cross-record source semantics. Database constraints enforce identities and
references. Low-level SQL writes are not a source-validation interface.

## Operations

All operations live in `knowledgebase/storage/operations.py`:

- `save_parent_child_chunks(session, chunks)`: accept a `ParentChildChunks`
  snapshot, insert and flush parents, then save children, metadata, and links.
- `save_chunks(session, chunks)`: continue accepting ordinary and flat structural
  chunks; additionally save `ChildChunk.parent_id` against an already stored parent.
- `get_parents(session, file_id)`: return `ParentChunk` snapshots ordered by the
  document-global parent index; missing or flat-only files return an empty list.
- `get_parents_by_ids(session, parent_ids)`: load existing parents once per ID;
  ignore missing IDs and do not promise requested order. Children that share a
  parent can supply duplicate IDs without returning duplicate parents.
- `get_chunks()` and `get_chunks_by_ids()`: restore `ChildChunk` when a link
  exists, `StructuredChunk` for flat structural records, and `Chunk` for MVP rows.
  Both preserve their previous ordering contracts.

These helpers flush without committing or changing file status. The caller owns
commit/rollback and can keep source, parents, children, and the Ready transition
in one transaction. Duplicate IDs or file/index pairs are insert errors, not
overwrites. After a failed flush, the caller must roll back the transaction.
Returned snapshots are independent of ORM records and may outlive the session.

Reads do not filter file status or implement retrieval expansion. The retrieval
layer restricts evidence to Ready files and controls deduplication,
ranking, and context budgets.

## Example

With a session factory named `sessions` after `init_db()`:

```python
from knowledgebase.rag.chunking import split_parent_child
from knowledgebase.rag.parsing import parse_markdown
from knowledgebase.storage.operations import (
    create_file, get_chunks, get_parents, get_parents_by_ids,
    save_document_source, save_parent_child_chunks,
)

text = "# Guide\n\nInstall the package.\n\n- Restart the server.\n"
blocks = parse_markdown(text)
chunks = split_parent_child(
    text, blocks, "guide-1",
    parent_max_tokens=64, child_max_tokens=16, encoding_name="cl100k_base",
)
with sessions.begin() as session:
    create_file(session, "guide-1", "guide.md")
    save_document_source(session, "guide-1", "md", text, blocks)
    save_parent_child_chunks(session, chunks)

with sessions() as session:
    children = get_chunks(session, "guide-1")
    parents = get_parents(session, "guide-1")
    selected_parents = get_parents_by_ids(session, [child.parent_id for child in children])

assert children == chunks.children
assert parents == chunks.parents
assert selected_parents == parents  # This example has one parent and two children.
```

This example leaves the file in Processing because it has no vector index.

## Cleanup and Compatibility

`delete_chunks(session, file_id)` deletes flat/child rows first. Foreign-key
cascades remove their structural metadata and parent links. The same helper then
deletes that file's parents. Repeated cleanup is a no-op and retains the complete
source until `delete_file_record()` removes the file. Childless parents also
cascade from file deletion, supporting cleanup of partially saved files.

The existing file deletion and interrupted-upload recovery services already use
`delete_chunks()`, so their cleanup now includes parent records. These operations
remain file-scoped and transactional in SQLite; SQLite and Chroma still do not
share a transaction. Historical answer snapshots remain independent and survive
source deletion.

`init_db()` adds missing tables to an MVP or flat-structural database without
rewriting existing columns or inventing parent relationships. This is schema
compatibility, not automatic conversion to parent-child indexing. Use isolated
data directories for v1 experiments as before.

## Verification

Run `uv run --locked python -m pytest tests/test_parent_child_storage.py`, or
`make test` for all backend checks. Tests use temporary SQLite files and offline
embeddings with a real local Chroma collection where lifecycle checks need one.
They cover fresh-engine persistence for TXT/Markdown, ordered and mixed-type reads,
source offsets and block metadata, detached snapshots, caller rollback, foreign
keys, duplicate identities, deletion/recovery scope, old-schema compatibility,
and historical answer evidence. No real provider requests are made.
