# Vector Database

`knowledgebase/storage/vectordb.py` provides a small `ChromaStore` around an
existing Chroma collection. The caller supplies vectors from the embedding
provider and creates the collection with its persistence path and distance metric.

- `upsert_chunks(chunks, embeddings)` stores chunk IDs, vectors, and `file_id`
  metadata. The chunk and embedding lists use matching positions. Existing IDs
  are updated; new IDs are inserted.
- `search(query_embedding, top_k=5, file_ids=None)` returns `VectorMatch` objects with `chunk_id`
  and `distance`, preserving Chroma's result order. Distances use the collection's
  configured metric. Smaller means nearer; distance is not an answer-confidence
  probability.
- Pass a nonempty `file_ids` list to restrict the search to those files before
  selecting the nearest results. `None` searches all files. The retrieval layer
  returns no evidence directly when there are no ready files to search.
- `delete_by_file_id(file_id)` removes all vectors with that file ID.

The wrapper passes requests directly to Chroma and lets its exceptions propagate.
It does not generate embeddings, copy canonical text, or manage SQLite records
and file status. SQLite retains the original chunk text and source offsets.
The [retrieval layer](retrieval.md) loads that text and restricts searches to
ready files.

## Local Example

Run `uv run python` from the repository root and enter this example. It uses
fixed two-dimensional vectors to demonstrate storage without a model API call:

```python
import chromadb

from knowledgebase.rag.chunking import split_text
from knowledgebase.storage.vectordb import ChromaStore

client = chromadb.PersistentClient(path="data/chroma")
collection = client.get_or_create_collection(
    name="example-chunks",
    embedding_function=None,
    configuration={"hnsw": {"space": "cosine"}},
)
store = ChromaStore(collection)
chunks = split_text("First. Second.", "example-file", chunk_size=7, overlap=0)
store.upsert_chunks(chunks, [[1.0, 0.0], [0.0, 1.0]])
print(store.search([1.0, 0.0], top_k=2))
store.delete_by_file_id("example-file")
```

Chroma persists data automatically. `data/` is ignored by Git. The example uses
cosine distance, where identical directions have distance zero. Use a separate
collection for actual model embeddings, consistently using the same model and
dimensions for documents and queries.

`make test` checks actual local Chroma writes, nearest-neighbor results, updates,
file-scoped deletion, and persisted data read from another process. The fixed
vectors verify storage behavior, not semantic retrieval quality.

References: [collection methods](https://docs.trychroma.com/reference/python/collection),
[collection configuration](https://docs.trychroma.com/docs/collections/configure),
and [persistent clients](https://docs.trychroma.com/docs/run-chroma/clients).
