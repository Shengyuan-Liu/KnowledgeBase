# Project Structure and Module Management

## Purpose and Status

Use one repository with a root-level `knowledgebase/` Python package and a separate `frontend/` React application. The Python package lives directly at the repository root, without a `src/` wrapper. Root-level `pyproject.toml` and `uv.lock` manage the backend; `frontend/package.json` and its lockfile manage the frontend.

This is a proposed implementation structure based on the [MVP technical plan](mvp/mvp-technical-plan.md) and [frontend design](mvp/mvp-frontend-design.md). The current Python entry point is a placeholder. Create modules as their behavior is implemented rather than adding the entire tree as empty scaffolding.

## Recommended Directory Tree

```text
KnowledgeBase/
├── README.md
├── AGENTS.md
├── pyproject.toml
├── uv.lock
├── .python-version
├── .env.example
├── .gitignore
├── docs/
│   ├── README.md
│   ├── project-structure.md
│   └── mvp/
│       ├── mvp-product-design.md
│       ├── mvp-technical-plan.md
│       ├── mvp-frontend-design.md
│       ├── mvp-system-design.md
│       ├── mvp-system-design.png
│       └── mvp-system-design.excalidraw
├── knowledgebase/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── schemas.py
│   ├── api/
│   │   ├── dependencies.py
│   │   ├── files.py
│   │   ├── chat.py
│   │   ├── conversations.py
│   │   └── streaming.py
│   ├── services/
│   │   ├── files.py
│   │   └── chat.py
│   ├── rag/
│   │   ├── chunking.py
│   │   ├── retrieval.py
│   │   ├── generation.py
│   │   └── citations.py
│   ├── providers/
│   │   ├── llm.py
│   │   └── embeddings.py
│   └── storage/
│       ├── database.py
│       ├── models.py
│       ├── repository.py
│       ├── vectordb.py
│       └── file_store.py
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── types.ts
│       ├── api/
│       │   ├── client.ts
│       │   ├── chatStream.ts
│       │   └── chatStream.test.ts
│       ├── hooks/
│       │   ├── useLibrary.ts
│       │   ├── useChat.ts
│       │   └── chatReducer.ts
│       ├── components/
│       │   ├── workspace/
│       │   ├── library/
│       │   ├── chat/
│       │   ├── evidence/
│       │   └── ui/
│       └── styles/
│           ├── tokens.css
│           └── global.css
├── tests/
│   ├── conftest.py
│   ├── fixtures/
│   ├── test_chunking.py
│   ├── test_file_lifecycle.py
│   ├── test_retrieval.py
│   ├── test_citations.py
│   ├── test_chat.py
│   └── test_api.py
├── evals/
│   ├── dataset.jsonl
│   ├── materials/
│   ├── run.py
│   └── results/
└── data/                         # Local runtime data; ignored by Git
    ├── knowledgebase.db
    ├── uploads/
    └── chroma/
```

Python subpackage `__init__.py` files and most frontend component, CSS Module, and test files are omitted for readability. The frontend retains Vite's conventional `src/` directory. When the backend is implemented, `knowledgebase/main.py` becomes its application entry point and replaces the root placeholder `main.py`.

## Backend Responsibilities

The function and type names below are suggested contracts, not existing APIs.

| Module | Responsibility | Suggested functions or types |
| --- | --- | --- |
| `main.py` | Build the FastAPI application, register routes, and manage startup and shutdown | `create_app()`, `lifespan()` |
| `config.py` | Load and validate paths, model settings, credentials, and operational limits | `Settings`, `get_settings()` |
| `schemas.py` | Define application-owned data contracts shared across modules | `Chunk`, `RetrievedChunk`, `Source`, request/response models, and application events |
| `api/dependencies.py` | Supply configured services, clients, and database sessions to routes | `get_file_service()`, `get_chat_service()` |
| `api/files.py` | Translate upload, list, and delete requests into service calls and HTTP responses | File route handlers |
| `api/chat.py` | Accept questions and expose the answer stream | Chat route handler |
| `api/conversations.py` | Return saved conversation state | Conversation route handler |
| `api/streaming.py` | Encode application events as SSE frames | `encode_sse()` |
| `services/files.py` | Coordinate ingestion, status transitions, failure cleanup, deletion, and restart recovery | `ingest_file()`, `delete_file()`, `recover_processing_files()` |
| `services/chat.py` | Coordinate history, question resolution, retrieval, generation, citation validation, and persistence | `stream_answer()` |
| `rag/chunking.py` | Split text while preserving stable chunk associations, ordering, and source offsets | `split_text()` |
| `rag/retrieval.py` | Embed a question, search vectors, check file eligibility, and load canonical evidence | `retrieve()` |
| `rag/generation.py` | Resolve follow-ups and generate answers from evidence; keep task prompts beside their use | `resolve_question()`, `stream_grounded_answer()` |
| `rag/citations.py` | Validate cited IDs and construct source records from stored source text | `validate_citations()`, `build_sources()` |
| `providers/llm.py` | Encapsulate the chosen provider SDK behind a small model-call interface | `LLMClient` interface and current implementation |
| `providers/embeddings.py` | Encapsulate document and query embedding calls | `embed_documents()`, `embed_query()` |
| `storage/database.py` | Configure SQLAlchemy engine and session creation | Engine and session factories |
| `storage/models.py` | Define SQLAlchemy table mappings | File, chunk, conversation, and message models |
| `storage/repository.py` | Read and write business records; keep database queries inside the storage boundary | File-state updates, chunk storage, history loading, and message persistence |
| `storage/vectordb.py` | Implement vector database operations and translate provider results into application-owned types; currently uses Chroma | `ChromaStore`, `upsert_chunks()`, `search()`, `delete_by_file_id()` |
| `storage/file_store.py` | Save, read, and delete retained original TXT files using application-owned file IDs | `save_text()`, `read_text()`, `delete_text()` |

Services decide the order of operations and recovery behavior. RAG modules implement individual processing steps. Provider and storage modules encapsulate external calls. Keep configuration explicit so the same service functions can run from API routes, tests, and evaluation scripts.

## Dependency and Data Boundaries

The main call direction is:

```text
API routes → Services → RAG steps → Model and storage interfaces
                     → Storage operations

Tests and evaluation runner → Services or individual RAG steps
```

- Keep HTTP-specific request objects, exceptions, and SSE encoding in `api/`. Services emit application-owned events rather than constructing HTTP responses.
- Pass repositories, vector stores, and model clients explicitly to the code that needs them. Assemble actual dependencies at the application boundary; tests can supply fake implementations.
- Keep `schemas.py` independent of API handlers and concrete provider or database implementations. Start with one small file and split it by responsibility only when needed.
- Keep SQLAlchemy ORM entities in the storage boundary. `storage/models.py` describes database tables; `schemas.py` describes data exchanged by the application.
- Convert Chroma results into application-owned retrieval results before returning them to RAG code. Preserve the metric name and score ordering meaning; scores are not correctness probabilities.
- Use absolute package imports such as `from knowledgebase.schemas import Source`. Configure package installation in `pyproject.toml` during implementation rather than modifying `sys.path`.
- Keep `__init__.py` files small and free of client creation or database initialization. Avoid circular imports and generic `utils.py` collections; place helpers beside the behavior they support.

### File Lifecycle

`services/files.py` owns the workflow from validation through chunking, embedding, persistence, and readiness. Mark a file `ready` only after all required writes succeed. Failed ingestion and abandoned processing work require explicit cleanup and a recoverable failure state.

The implemented [ingestion workflow](file-ingestion.md) preserves source text in SQLite chunks. `FileStore` is optional and is not used to save a second copy during ingestion.

SQLite determines retrieval eligibility. `rag/retrieval.py` must ensure that returned evidence belongs to ready files and resolve canonical text from business storage. Do not assume every Chroma hit is eligible, or let ineligible hits silently consume all available retrieval slots.

Deletion first makes the file ineligible, then removes vectors, chunks, and the file record, plus any optional original TXT copy. Report success only after cleanup completes. Keep partial failures retryable because SQLite, Chroma, and the filesystem do not share one transaction.

### Question Answering

`services/chat.py` should make this sequence easy to read:

```text
Load history
    → Resolve follow-up question
    → Retrieve current eligible evidence
    → Generate answer
    → Validate citations and finalize sources
    → Persist completed exchange
    → Emit completion
```

History helps interpret the question but does not supply factual evidence. Handle empty retrieval explicitly. Nonempty results still require evidence-grounded generation and evaluation; source-ID membership alone does not prove answer support.

Stream deltas during generation, then reconcile them with the finalized answer and validated source mappings. The current [streaming implementation](chat-streaming.md) saves only completed exchanges; failed or interrupted partial text remains client-side. Correlate events with request IDs until completion supplies persistent conversation/message IDs. Keep the `start`, `answer_delta`, `sources`, `debug`, `complete`, and `error` contracts aligned with the [frontend specification](mvp/mvp-frontend-design.md#api-and-stream-contract).

## Frontend Organization

| Area | Responsibility |
| --- | --- |
| `api/client.ts` | Ordinary HTTP requests, typed payloads, and consistent HTTP errors |
| `api/chatStream.ts` | Streaming UTF-8 decoding, incremental SSE parsing, cancellation, and stream errors |
| `hooks/useLibrary.ts` | File loading, upload/delete results, and polling while processing continues |
| `hooks/useChat.ts`, `chatReducer.ts` | Conversation lifecycle, message updates, stale-event rejection, and pending/streaming/completed/failed/interrupted states |
| `components/workspace/` | Workspace composition, responsive panels, and drawers |
| `components/library/` | File list, file rows, upload control, and deletion interaction |
| `components/chat/` | Message list, answer cards, composer, and answer-specific debug details |
| `components/evidence/` | Citation controls, expandable source lists, and the Evidence panel |
| `components/ui/` | Small reusable controls that are actually needed, such as dialogs and disclosures |
| `types.ts` | Frontend request, file, message, source, and discriminated stream-event types |
| `styles/` | Shared visual tokens and global defaults; component styles live in adjacent CSS Modules |

Keep server file state, conversation state, and presentation state distinct. Source records belong to their messages. The source list and Evidence panel share those records and select evidence by `(messageId, sourceId)`. Local file search changes the displayed library only, not retrieval scope.

Place component and reducer tests next to their implementation. Use React state and reducers for the MVP. Keep provider credentials and all embedding, vector search, and model calls on the backend.

## Tests, Evaluation, and Version Control

- Use `tests/` for deterministic backend verification, including chunk positions, invalid uploads, partial-write cleanup, ready-file eligibility, deletion, citation associations, conversation behavior, and API streaming. Isolate test storage with temporary directories and use fake models where appropriate.
- Use `evals/` for a fixed set of materials, questions, expected evidence, and key answer points. The runner calls the same services used by the API. Measure evidence retrieval separately from answer support, and record latency, model identifiers, embedding configuration, chunking, and retrieval settings.
- Verify the full upload-to-answer path with real embedding and LLM providers before MVP delivery. Mock tests establish behavior, not real retrieval or answer quality.
- Commit dependency lockfiles and an `.env.example` containing placeholders. Ignore `.env`, runtime `data/`, virtual environments, frontend dependencies, build artifacts, and caches when those files are introduced. Do not commit credentials or private uploads.
- Commit selected non-sensitive evaluation baselines and their configurations when useful for comparison. Keep private or transient results outside version control.
- Complete each coherent change with relevant checks and an English Git commit. Code changes require relevant tests and applicable verification. Documentation-only changes require content, link, and formatting review, including `git diff --check`.
- Keep project documentation, prompts, comments, UI text, examples, and commit messages in English.

## Implementation Order and Growth

Build a working path incrementally:

1. Define the data contracts needed for text chunking, then implement chunking and source-offset tests.
2. Add file/chunk storage and processing-state operations.
3. Add embedding integration, Chroma, and retrieval with eligibility checks.
4. Complete ingestion, deletion, restart recovery, and failure cleanup.
5. Add grounded answers, follow-up resolution, citations, and the fixed evaluation runner.
6. Expose the HTTP/SSE contracts, connect the React UI, and verify the integrated workflow.

The user intends to write most Python implementation code by hand. Use these responsibilities and function contracts as implementation guidance; follow the repository's [code ownership instructions](../AGENTS.md) when making code changes.

Ordinary Python functions are sufficient for the MVP workflow. Add Markdown/PDF parsing in V2, hybrid retrieval and reranking in V3, and agent capabilities when V4 requirements justify them. Introduce new directories when concrete behavior needs them. A general plugin framework, unused storage adapters, and a preemptive `agents/` layer are outside this structure's current needs.
