# File Ingestion

`knowledgebase/services/files.py` provides `ingest_file` for indexing TXT/Markdown content.
It accepts the original filename and bytes, a SQLAlchemy session factory, an
`EmbeddingClient`, and a `ChromaStore`. It returns the generated file ID after
successful indexing.

## Workflow

1. Require a `.txt` or `.md` extension (case-insensitive), decode UTF-8, and reject empty
   or whitespace-only content. `InvalidUploadError` (a `ValueError` subclass)
   propagates before a file record is created, including invalid UTF-8 input.
2. Generate a file ID and commit a `processing` record, preserving the filename.
3. Parse the unchanged text with `parse_txt` or `parse_markdown`, then chunk it
   using the selected strategy. The default is parent-child chunking with
   512-token children, 1536-token parents, `cl100k_base` counting, and no overlap.
   Only children are embedded; parent context is expanded during retrieval.
   Explicit `structural` mode retains flat 512-token structural chunks. Explicit
   `character` mode retains the MVP's 2048-character size and 256-character overlap.
4. Embed the chunk texts in one provider call.
5. Save the complete source, hash, parser blocks, chunks and structural metadata;
   write vectors and mark the file `ready`. All SQLite writes in this step share
   one transaction. SQLite and Chroma do not share a transaction.

Original text and exact chunk offsets are retained in SQLite, including in
character mode. This workflow does not save a separate uploaded file on disk.
Each upload gets a new ID,
including uploads with the same filename.

If parsing, chunking, embedding, or final persistence fails, source/chunk writes
are absent or roll back together, including structural metadata.
The service marks the file `failed`, stores the error message, removes vectors
for that file ID, and propagates the exception. Other files remain unchanged.
Cleanup errors also propagate; this function does not implement automatic retries
or recovery after process termination.

## Usage

With a configured session factory and model/vector clients:

```python
from pathlib import Path

from knowledgebase.rag.retrieval import retrieve
from knowledgebase.services.files import ingest_file

path = Path("notes.md")
file_id = ingest_file(
    file_name=path.name,
    content=path.read_bytes(),
    session_factory=session_factory,
    embedding_client=embedding_client,
    vector_store=vector_store,
)

with session_factory() as session:
    results = retrieve("What do the notes explain?", session, embedding_client, vector_store)
    for result in results:
        print(result.chunk.text, result.distance)
```

The service owns its database transactions. Pass a session factory rather than
an existing session. With real OpenAI clients, launch Python using
`uv run --env-file .env python`. Each document embedding call contains all chunks;
the provider's request limits apply.

API, CLI, and evaluation entry points pass the shared [Settings](configuration.md)
to this service. Direct callers can supply `chunking_strategy`, `chunk_max_tokens`,
and `chunk_tokenizer`, or `chunk_size`/`overlap` for character mode. Changing these
options affects only new uploads. The default parent-child strategy is a functional baseline;
live quality comparisons remain separate work.

See [embedding setup](embeddings.md), [vector database setup](vectordb.md),
[retrieval](retrieval.md), [file deletion](file-deletion.md), and the
[file management API](file-api.md). Restart recovery remains a separate step.

## Verification

`make test` verifies ingestion through retrieval using real temporary SQLite and
Chroma databases with fixed embeddings. It also covers UTF-8 and TXT/MD validation,
source preservation, distinct upload IDs, observable processing state, embedding
failure, parser failure, partial vector writes, rollback of source/metadata, and
failure of the ready transition. These tests
verify workflow behavior, not semantic retrieval quality with a live model.
