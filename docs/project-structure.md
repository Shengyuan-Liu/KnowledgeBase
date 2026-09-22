# Project Structure and Module Management

## Current Status

The repository contains a working Python backend, interactive CLI, HTTP/SSE API,
and frozen-corpus evaluation runner. The root `main.py` launches the CLI;
`knowledgebase/api/app.py` creates the FastAPI application. The React
[frontend workspace](frontend.md) implements the responsive layout and file
management, streaming chat, evidence navigation, and conversation restoration.

Use the root `knowledgebase/` package without a `src/` wrapper. `pyproject.toml`
and `uv.lock` manage Python dependencies. The `frontend/` directory owns
its TypeScript dependencies and Vite configuration.

## Implemented Directory Layout

```text
KnowledgeBase/
├── main.py                      # Interactive CLI entry point
├── pyproject.toml
├── uv.lock
├── Makefile
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.ts
│   ├── playwright.config.ts
│   ├── src/                    # React UI, file API client, and component tests
│   └── e2e/                    # Browser tests against isolated FastAPI storage
├── knowledgebase/
│   ├── cli.py
│   ├── config.py
│   ├── schemas.py
│   ├── api/
│   │   ├── app.py
│   │   ├── dependencies.py
│   │   ├── files.py
│   │   ├── chat.py
│   │   ├── conversations.py
│   │   └── streaming.py
│   ├── services/
│   │   ├── files.py
│   │   └── chat.py
│   ├── rag/
│   │   ├── parsing.py           # Standalone v1 source parser; not yet wired into ingestion
│   │   ├── chunking.py
│   │   ├── retrieval.py
│   │   ├── context.py
│   │   ├── query.py
│   │   ├── generation.py
│   │   └── citations.py
│   ├── providers/
│   │   ├── llm.py
│   │   └── embeddings.py
│   └── storage/
│       ├── runtime.py
│       ├── database.py
│       ├── models.py
│       ├── operations.py
│       └── vectordb.py
├── tests/
│   ├── conftest.py
│   ├── frontend_server.py       # Offline server for browser acceptance tests
│   └── test_*.py
├── evals/
│   ├── evaluate.py
│   ├── nyu-test-cases.jsonl
│   ├── materials/
│   └── runs/
├── docs/
│   ├── README.md
│   └── mvp/
└── data/                        # Local runtime data; ignored by Git
    ├── knowledgebase.db
    └── chroma/
```

Package markers and individual documentation/test files are omitted for readability.
There is no retained upload directory: canonical source text lives in SQLite chunks.

## Responsibilities

| Module | Responsibility |
| --- | --- |
| `cli.py` | Parse terminal options, ingest supplied files, and run the conversation loop |
| `config.py` | Read credentials and the data directory from environment variables or `.env` |
| `schemas.py` | Define data snapshots, requests, responses, and stream events independently of ORM and HTTP handlers |
| `api/app.py` | Assemble the app, register routes, and own storage/SDK lifetimes |
| `api/dependencies.py` | Define one `AppResources` object and expose it to all routes |
| `api/files.py` | Translate file upload/list/delete operations into HTTP responses |
| `api/chat.py` | Expose complete JSON answers and SSE answers |
| `api/conversations.py` | Return ordered saved messages and historical evidence |
| `api/streaming.py` | Encode SSE frames and cancel generation on disconnect |
| `services/files.py` | Coordinate ingestion, file states, failure cleanup, and retryable deletion |
| `services/chat.py` | Coordinate history, retrieval, generation, citations, and atomic exchange persistence |
| `rag/parsing.py` | Parse TXT/Markdown into exact source blocks with heading metadata; standalone v1 component |
| `rag/chunking.py` | MVP character splitting and standalone v1 structural/token-budget chunking with exact source offsets |
| `rag/retrieval.py` | Restrict vector search to ready files and return canonical chunks with filenames |
| `rag/context.py` | Format numbered evidence without altering source text |
| `rag/query.py` | Resolve follow-up references using message history |
| `rag/generation.py` | Share the evidence-grounded prompt across synchronous and streamed generation |
| `rag/citations.py` | Check citation-number membership without claiming factual support |
| `providers/llm.py` | Wrap sync generation and async streaming SDK calls |
| `providers/embeddings.py` | Embed documents and questions using the same embedding model |
| `storage/runtime.py` | Open the same SQLite/Chroma configuration for API and CLI, then dispose the SQL engine on exit |
| `storage/database.py` | Create engines and session factories, enable SQLite foreign keys, and initialize tables |
| `storage/models.py` | Map files, chunks, conversations, messages, and answer snapshots |
| `storage/operations.py` | Query/write business records; flush writes while leaving commit to callers |
| `storage/vectordb.py` | Translate Chroma insert/search/delete calls into application types |
| `evals/evaluate.py` | Record isolated experiments, grade answers, and produce auditable reports/comparisons |

The evaluation runner intentionally owns a fresh index for each run, with its own
collection name and evaluation timeout/retry policy. Model, chunking, and retrieval
defaults come from the same [Settings and `.env`](configuration.md) as the API/CLI;
explicit experiment flags override them. It does not open the user's API/CLI library.

## Dependency and Data Boundaries

```text
API / CLI / evaluation → Services → RAG steps → Providers and storage
API conversation reads → Storage operations
```

- Routes depend on `api/dependencies.py`, not on another route module. Services do
  not construct HTTP responses or SSE frames.
- API and CLI share `open_storage(data_dir)`. Their SDK clients stay at their entry
  points. Imports do not create clients, open databases, or read credentials.
- Source eligibility and canonical text come from SQLite; Chroma stores vectors
  and file IDs. Retrieval carries filenames forward so answer assembly does not
  query the complete file list again.
- ORM records remain inside storage. Pydantic snapshots can outlive a session.
- Use absolute package imports. Keep `__init__.py` files free of initialization and
  avoid generic utility modules or provider factory hierarchies without a need.

## File and Answer Lifecycles

[Ingestion](file-ingestion.md) marks a file ready only after chunk/vector writes
succeed. [Deletion](file-deletion.md) commits retrieval exclusion before removing
vectors, then deletes chunks and the file record together. Partial cleanup remains
retryable because SQLite and Chroma do not share a transaction. Recovery of abandoned
processing records after a crash remains unimplemented.

[Chat](conversation-chat.md) loads history, resolves the question, retrieves fresh
evidence, generates an answer, checks citation numbers, and saves the original
question, answer, and source snapshot in one transaction. History helps resolve
references; it is not evidence for a new answer. Historical source snapshots survive
file deletion and carry a current deletion flag when read.

The [streaming endpoint](chat-streaming.md) correlates events by request ID until
completion provides persisted conversation/message IDs. Failed/interrupted partial
text remains client-side. The [frontend contract](mvp/mvp-frontend-design.md#api-and-stream-contract)
defines reconciliation and interruption behavior.

## Tests and Development

`tests/conftest.py` provides function-scoped temporary storage, offline embeddings,
and API setup. Specialized tests retain local fixtures for behavior such as stream
cancellation or a database before initialization. No storage is shared across tests.
Run `make test`; opt-in live checks use `make test-live`.

Runtime dependencies exclude notebook tooling. Install it explicitly with
`uv sync --group notebooks` when needed. `.env` contains local secrets and stays
out of Git; `.env.example` contains placeholders.

Keep the [MVP scope](mvp/mvp-product-design.md): English-only, single-user TXT basic
RAG. The browser workflow is verified against the real API with offline provider
fixtures. Live-provider quality and production hosting need separate verification.
Add functionality and modules when current requirements justify them.
Follow [AGENTS.md](../AGENTS.md) for Python ownership, verification, English text,
and a Git commit for each completed change.

The local release can be started with `make app`, which serves the built UI and API
from one origin. Storage startup uses one process owner per data directory and
recovers interrupted uploads; see the [file API guide](file-api.md).
