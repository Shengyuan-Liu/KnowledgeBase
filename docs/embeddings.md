# Embedding Provider

`knowledgebase/providers/embeddings.py` wraps the OpenAI Python SDK in an
`EmbeddingClient`. It converts text into vectors; callers handle chunk IDs,
storage, file status, and retrieval.

- `embed_documents(texts)` sends a batch to OpenAI and extracts vectors in the
  returned order.
- `embed_query(text)` returns one vector using the same model.
- The default model is `text-embedding-3-small`. Pass another model explicitly
  when constructing the wrapper. Rebuild the vector index when changing models.
- Inputs are passed through unchanged, including whitespace and empty inputs.
- Each call sends one batch. The SDK and API handle input validation and service
  limits. There is no local validation, automatic batching, or truncation.
- Vectors are extracted directly without sorting or response checks. SDK
  exceptions propagate to the caller.
- The caller creates and closes the SDK client and controls its timeout and
  retry settings. No client or network connection is created at import time.

## Local Usage

Keep `OPENAI_API_KEY` in the ignored `.env` file. `.env.example` contains
only the variable name. Load the local file when launching Python:

```sh
uv run --env-file .env python
```

Then run this example in the Python session. It makes two live API requests:

```python
from openai import OpenAI

from knowledgebase.providers.embeddings import EmbeddingClient

with OpenAI(timeout=30.0, max_retries=2) as sdk:
    embeddings = EmbeddingClient(sdk)
    vectors = embeddings.embed_documents(["A library stores books."])
    query = embeddings.embed_query("Where can I find books?")
    print(len(vectors), len(vectors[0]), len(query))
```

`make test` runs deterministic tests without credentials or live requests,
including one test of the actual SDK through a simulated HTTP transport.
These tests verify integration behavior, not retrieval quality.

References: [OpenAI embeddings guide](https://developers.openai.com/api/docs/guides/embeddings)
and [create embeddings API reference](https://developers.openai.com/api/reference/resources/embeddings/methods/create).
