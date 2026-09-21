# Embedding Provider

`knowledgebase/providers/embeddings.py` wraps the OpenAI Python SDK in an
`EmbeddingClient`. It converts text into vectors; callers handle chunk IDs,
storage, file status, and retrieval.

- `embed_documents(texts)` sends a batch to OpenAI and extracts vectors in the
  returned order.
- `embed_query(text)` returns one vector using the same model.
- The default model is `text-embedding-3-small`. API/CLI/evaluations pass
  `EMBEDDING_MODEL` from [runtime configuration](configuration.md). Direct Python
  callers pass their chosen model explicitly. Use a fresh index when changing models.
- Inputs are passed through unchanged, including whitespace and empty inputs.
- Each call sends one batch. The SDK and API handle input validation and service
  limits. There is no local validation, automatic batching, or truncation.
- Vectors are extracted directly without sorting or response checks. SDK
  exceptions propagate to the caller.
- The caller creates and closes the SDK client and controls its timeout and
  retry settings. No client or network connection is created at import time.

## Local Usage

Keep `OPENAI_API_KEY` and the model settings in the ignored `.env` file.
`.env.example` lists all available settings. Start Python from the repository root:

```sh
uv run --locked python
```

Then run this example in the Python session. It makes two live API requests:

```python
from openai import OpenAI

from knowledgebase.config import Settings
from knowledgebase.providers.embeddings import EmbeddingClient

settings = Settings()
with OpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
    timeout=settings.openai_timeout_seconds,
    max_retries=settings.openai_max_retries,
) as sdk:
    embeddings = EmbeddingClient(sdk, model=settings.embedding_model)
    vectors = embeddings.embed_documents(["A library stores books."])
    query = embeddings.embed_query("Where can I find books?")
    print(len(vectors), len(vectors[0]), len(query))
```

`make test` runs deterministic tests without credentials or live requests,
including one test of the actual SDK through a simulated HTTP transport.
These tests verify integration behavior, not retrieval quality.

References: [OpenAI embeddings guide](https://developers.openai.com/api/docs/guides/embeddings)
and [create embeddings API reference](https://developers.openai.com/api/reference/resources/embeddings/methods/create).
