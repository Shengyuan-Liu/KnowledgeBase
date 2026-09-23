# Retrieval

`knowledgebase/rag/retrieval.py` connects query embeddings, vector search, and
canonical chunk text:

1. Read files from SQLite and select those with status `ready`.
2. If none are ready, return `[]` without an embedding request or vector search.
3. Embed the question through the supplied `EmbeddingClient`.
4. Search Chroma with a file ID filter and the requested `top_k`.
5. Load the matched chunks from SQLite with `get_chunks_by_ids`.
6. Order selected candidates by distance, breaking ties by chunk ID. Expand child
   hits to parents, deduplicate parent IDs, and pack whole regions within the
   numbered evidence budget.
7. Return the packed `RetrievedChunk` objects. Use `retrieve_evidence()` to also
   inspect candidates, exclusions, and token counts.

Filtering applies before nearest-neighbor selection, so processing and failed
files cannot consume result slots. Chroma stores file IDs as metadata; SQLite
supplies file status and canonical text. The ingestion workflow is responsible
for keeping those records associated.

## Calling the Function

With an existing SQLAlchemy session, embedding client, and Chroma store:

```python
from knowledgebase.rag.retrieval import retrieve

results = retrieve(
    question="Where can I find books?",
    session=session,
    embedding_client=embedding_client,
    vector_store=vector_store,
    top_k=5,
)
for result in results:
    print(result.chunk.file_id, result.chunk.text, result.distance)
```

Each result contains a full `Chunk` (including its ID and original text offsets),
the filename from the already loaded file metadata, and the raw distance reported
by the collection (the best matched child's distance for a parent). Answer assembly reuses this filename instead of querying all
files a second time. Smaller distances are nearer;
they are not probabilities of answer correctness. No matches or no fitting regions
returns `[]`. See [parent-child retrieval](parent-child-retrieval.md) for expansion,
source metadata, and the `EVIDENCE_MAX_TOKENS` packing contract.

The caller owns the session and model client. Retrieval does not commit, update
file status, or generate an answer. Dependency exceptions propagate normally.

`get_chunks_by_ids(session, chunk_ids)` loads existing chunks in one SQL query.
It returns data snapshots without promising input order or filtering file status;
retrieval maps them by ID before ranking and expansion.

## Verification

`make test` covers file filtering before `top_k`, original text and offsets,
ranking and distances, and empty retrieval. Tests use real local SQLite and
Chroma with a fixed query embedding, without a model API call. They verify
retrieval behavior, not semantic retrieval quality.

See [embedding setup](embeddings.md), [vector database setup](vectordb.md), and
[Chroma metadata filtering](https://docs.trychroma.com/docs/querying-collections/metadata-filtering).
