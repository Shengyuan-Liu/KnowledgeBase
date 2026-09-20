# File Deletion

`knowledgebase/services/files.py` provides `delete_file(file_id, session_factory,
vector_store)`. It removes an ingested file's vectors, canonical chunks, and file
record, returning `None` only after cleanup completes. It makes no model calls.

## Transaction boundaries

1. Mark the file `failed` with `Deletion pending. Retry deletion to finish cleanup.`
   and commit. This reuses the existing non-ready state; retrieval excludes the
   file before any vector cleanup starts.
2. Delete its vectors through `ChromaStore.delete_by_file_id`.
3. In one SQLite transaction, call `delete_chunks` and then `delete_file_record`.
   Chunks must be removed first because they reference the file through a foreign key.

The storage helpers flush their changes but never commit. The service owns the
transactions. SQLite and Chroma have no shared transaction, so the first committed
state makes residual data ineligible while cleanup is incomplete.

If vector deletion fails, the exception propagates and the failed file and chunks
remain. If the final SQLite transaction fails, chunk/file changes roll back while
the vectors may already be gone. In both cases, explicitly call `delete_file` with
the same ID again: removing already absent vectors is safe. The pending message
remains until the file record is removed. There are no automatic retries.

A missing file raises `LookupError` before touching Chroma, including a repeated
request after successful deletion. Other file IDs remain unchanged, even if they
have the same filename. A failed ingestion record with no chunks/vectors can also
be deleted.

## Usage

With the session factory and vector store used for ingestion:

```python
from knowledgebase.services.files import delete_file

delete_file(file_id, session_factory, vector_store)
```

This is a synchronous service operation. Serialize ingestion and deletion for the
same file; it does not cancel active ingestion or answers that already loaded their
sources. New retrievals after the first commit exclude the file, including when
cleanup fails. Deleting the last ready file causes subsequent questions to return
the existing insufficient-evidence response without embedding or generation calls.

The current ingestion service does not retain a separate original TXT copy, so
deletion does not use the optional `FileStore` utility. CLI commands, HTTP routes,
and UI controls for deletion are separate work.

## Verification

`make test` covers caller-owned commit/rollback, deletion scoped to one file,
ingest → ask → delete → ask, exclusion before vector cleanup, partial vector
deletion failure, SQLite cleanup rollback, and explicit retry. Tests use real
temporary SQLite and Chroma stores with offline embedding and LLM doubles.
