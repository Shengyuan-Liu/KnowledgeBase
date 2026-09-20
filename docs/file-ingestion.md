# File Ingestion

`knowledgebase/services/files.py` provides `ingest_file` for indexing TXT content.
It accepts the original filename and bytes, a SQLAlchemy session factory, an
`EmbeddingClient`, and a `ChromaStore`. It returns the generated file ID after
successful indexing.

## Workflow

1. Require a `.txt` extension (case-insensitive), decode UTF-8, and reject empty
   or whitespace-only content. Validation errors propagate before a file record
   is created.
2. Generate a file ID and split the unchanged text using `chunk_size` and
   `overlap`, defaulting to 256 and 64 characters.
3. Create and commit a `processing` file record, preserving its original filename.
4. Embed the chunk texts in one provider call.
5. Save chunks, write vectors, and mark the file `ready`. Chunk writes and the
   ready transition share one SQLite transaction.

Original text is retained in SQLite chunks with source offsets. This workflow
does not save a separate TXT copy or use `FileStore`. Each upload gets a new ID,
including uploads with the same filename.

If embedding or final persistence fails, the chunk transaction rolls back.
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

path = Path("notes.txt")
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

See [embedding setup](embeddings.md), [vector database setup](vectordb.md),
[retrieval](retrieval.md), and [file deletion](file-deletion.md). Restart recovery
and HTTP upload routes remain separate implementation steps.

## Verification

`make test` verifies ingestion through retrieval using real temporary SQLite and
Chroma databases with fixed embeddings. It also covers UTF-8 and TXT validation,
source preservation, distinct upload IDs, observable processing state, embedding
failure, partial vector writes, and failure of the ready transition. These tests
verify workflow behavior, not semantic retrieval quality with a live model.
