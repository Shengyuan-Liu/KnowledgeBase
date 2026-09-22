# Document and Structural Chunk Storage

Status: implemented as a v1 storage building block. The parser and structural
chunker can now persist their output, but the upload service still accepts TXT
and invokes the MVP character splitter. No existing library has been reindexed.

## Data Model

The existing `files` and `chunks` columns remain unchanged. Two supplementary
tables retain v1 information without requiring column migrations for MVP data:

| Table | Key | Stored information |
| --- | --- | --- |
| `files` | `file_id` | Existing filename, lifecycle state, timestamp, and error |
| `document_sources` | `file_id`, referencing `files` | Format (`txt` or `md`), complete decoded text, source hash, ordered parser blocks |
| `chunks` | `chunk_id` | Existing file association, exact excerpt, order, and source offsets |
| `chunk_structures` | `chunk_id`, referencing `chunks` | Heading path, source block indices, token count, tokenizer, and token limit |

`DocumentSourceRecord` and `ChunkStructureRecord` in
`knowledgebase/storage/models.py` define the two new database tables.
`DocumentSource` and `StructuredChunk` in `knowledgebase/schemas.py` are independent
in-memory snapshots returned to callers, not ORM objects or new HTTP contracts.

The ordered `SourceBlock` list is stored as JSON, including each block's original
text, type, offsets, heading path, and heading level. A chunk's
`source_block_indices` refer to positions in that file's stored list. This retains
the meaning of those associations without requiring the parser to run again.

The source hash is SHA-256 of `text.encode("utf-8")`. There is no whitespace or
newline normalization: LF and CRLF sources have different hashes. Hashes identify
the canonical text; this step does not use them to deduplicate uploads.

Token configuration is stored per structural chunk, matching the existing
`StructuredChunk` fields. Source records with no chunks have no recorded token
configuration yet. Full ingestion-run provenance and parent-child records are
outside this storage step.

## Operations and Transaction Ownership

`knowledgebase/storage/operations.py` provides:

- `save_document_source(session, file_id, source_format, text, blocks)`: insert
  one source for an existing file, calculate its hash, and save the ordered blocks.
- `get_document_source(session, file_id)`: return a `DocumentSource`, or `None`
  for a missing file or an MVP file without a canonical document record.
- `save_chunks(session, chunks)`: save the common chunk fields, followed by
  structural metadata for any `StructuredChunk` inputs. Ordinary MVP `Chunk`
  inputs continue to work and do not acquire invented structural metadata.
- `get_chunks(session, file_id)`: return ordered chunks, restoring
  `StructuredChunk` when structural metadata exists and `Chunk` otherwise.
- `get_chunks_by_ids(session, chunk_ids)`: preserve the same data-model behavior
  for selected IDs; requested order is not guaranteed.

Writes flush but do not commit. Duplicate identities are insert errors rather
than updates. The caller can save the file, source, chunks, and lifecycle changes
in one transaction and roll all of them back together. Database foreign keys and
existing uniqueness constraints remain responsible for record identity.

Callers supply blocks parsed from the same canonical text and chunks produced
from those blocks. Storage does not reparse text or rerun tokenization. Reading
stored chunks does not imply the file is Ready; retrieval still applies that filter.
Mutating a returned snapshot does not modify database records.

## Example

With a session factory created by `build_session_factory()` after `init_db()`:

```python
from knowledgebase.rag.chunking import split_structured
from knowledgebase.rag.parsing import parse_markdown
from knowledgebase.storage.operations import (
    create_file, get_chunks, get_document_source, save_chunks, save_document_source,
)

text = "# Guide\n\nInstall the package.\n"
blocks = parse_markdown(text)
chunks = split_structured(
    text, blocks, "example-file", max_tokens=128, encoding_name="cl100k_base",
)

with sessions.begin() as session:
    create_file(session, "example-file", "guide.md")
    save_document_source(session, "example-file", "md", text, blocks)
    save_chunks(session, chunks)

with sessions() as session:
    source = get_document_source(session, "example-file")
    saved_chunks = get_chunks(session, "example-file")

assert source.text == text
assert source.blocks == blocks
assert saved_chunks == chunks
```

The example remains in `processing` because it does not create embeddings or a
vector index. The future ingestion service must mark Ready only after indexing.

## Deletion and Existing Data

`delete_chunks()` removes associated `chunk_structures` rows through the database
foreign key's `ON DELETE CASCADE`. `delete_file_record()` similarly removes the
file's `document_sources` row. The existing delete service still excludes the
file, deletes vectors, and removes chunks before the file record. If that SQLite
transaction rolls back, both source and metadata deletions roll back with it.

Deleting chunks alone leaves the source attached to the file, which can still be
failed or awaiting cleanup. Deleting a source-only failed file is supported.
Historical answer snapshots retain their original excerpts independently of these
tables and are not removed when a source file is deleted.

`init_db()` creates the supplementary tables in an older schema without rewriting
its original file/chunk rows or backfilling metadata. This is schema compatibility,
not conversion to v1 indexing. Continue v1 development in a fresh isolated data
directory as specified in the [technical plan](v1/v1-technical-plan.md); the
existing MVP library remains separate.

## Verification

Run `uv run --locked python -m pytest tests/test_document_storage.py` for source and
metadata storage checks, and `make test` for backend regressions. Tests use
temporary SQLite databases, with a real local Chroma collection for the deletion
service check. They verify TXT/MD persistence after reconnection, Unicode and CRLF
preservation, source-block associations, mixed MVP/v1 reads, caller rollback,
deletion scope, old-schema initialization, and historical evidence preservation.

This verifies persistence and lifecycle behavior, not retrieval quality. Markdown
uploads, shared ingestion configuration, and API/UI exposure of structural metadata
remain later integration work.
