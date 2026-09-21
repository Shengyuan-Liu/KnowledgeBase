# Personal Knowledge Base MVP Technical Plan

## Scope and Decisions

This plan implements the [MVP product design](mvp-product-design.md): a single-user knowledge base for uploading UTF-8 TXT files and asking questions with supporting source excerpts. The local MVP is implemented. The root README describes startup; the linked module guides document behavior and limitations.

Use a dedicated React frontend and a Python backend. Keep ingestion, retrieval, model calls, and storage separate enough to test independently and replace individual components later.

Existing data may be discarded when replacing a database. Data migration tooling and Alembic are outside the MVP scope. A future replacement may require rebuilding tables and reimporting source files.

## Technology Stack

| Area | Choice | Responsibility |
| --- | --- | --- |
| Frontend language | TypeScript | Define message, file, source, and stream event types |
| Frontend UI | React | Build the chat page, file list, source excerpts, and debug panel |
| Frontend tooling | Vite | Run the development server and create production assets |
| Styling | CSS Modules | Style components with locally scoped CSS |
| Frontend state | React useState / useReducer | Manage the current conversation, uploads, and stream lifecycle |
| HTTP and streaming | fetch with Server-Sent Events (SSE) | Call backend endpoints and consume incremental answers |
| Backend | Python + FastAPI | Handle uploads, file operations, conversations, and streamed answers |
| Data validation | Pydantic | Validate configuration, requests, and structured responses |
| RAG orchestration | Ordinary Python functions | Coordinate question resolution, retrieval, and grounded generation |
| Business storage | SQLite + SQLAlchemy | Store file state, canonical chunks, conversations, and messages |
| Vector storage | Chroma with local persistence | Store embeddings and source identifiers, and retrieve similar chunks |
| Model integration | Provider SDKs behind small interfaces | Call an LLM and an embedding model independently |
| Python environment | uv | Manage Python dependencies and execution |
| Backend tests | pytest | Test ingestion, retrieval, citations, deletion, and API behavior |
| Frontend tests | Vitest + React Testing Library | Test file states, chat interactions, sources, and streaming errors |
| Evaluation | A small Python runner and fixed dataset | Compare retrieval quality, answer support, and latency |

The implementation uses OpenAI `gpt-4.1-mini` for answers and reference resolution, configurable with `ANSWER_MODEL`, and `text-embedding-3-small` for embeddings. Keep credentials on the backend. Record model identifiers and relevant settings in evaluation results. Use one consistent embedding configuration for both documents and queries within an index; changing the embedding model requires rebuilding that index.

## Application Structure

```text
React browser application
        |
        | HTTP requests and SSE responses
        v
FastAPI backend
        |
        +-- File ingestion and deletion
        +-- RAG question-answering service
        +-- Model provider interfaces
        +-- Business storage --> SQLAlchemy --> SQLite
        +-- Vector storage ------------------> Chroma
```

API handlers translate HTTP input and output. Python services own the product behavior and can run without the frontend, including from tests and the evaluation runner.

Keep a small vector storage interface for inserting chunks, searching, and deleting by file ID. Return application-owned retrieval results instead of passing Chroma-specific objects into the chat service or frontend. Avoid building a general plugin framework or implementing unused database adapters.

## Main Workflows

### File Ingestion and Deletion

1. Validate the extension, UTF-8 encoding, and nonempty text. Return clear errors for unsupported or invalid input.
2. Assign a stable file ID and create a `processing` record in SQLite. Retain source text in the stored chunks; a separate original TXT copy is optional and is not written by the current ingestion workflow.
3. Split text into chunks with configurable size and overlap. Preserve stable chunk IDs, file associations, ordering, and source offsets so excerpts can be reconstructed.
4. Generate embeddings and write the vectors to Chroma. Store canonical chunk text and source metadata in SQLite.
5. Mark the file `ready` only after all required writes succeed. On failure, mark it `failed` and clean up partial index records.

Small TXT uploads are indexed synchronously within their request; the UI displays pending state and polls any processing records. Startup marks abandoned `processing` records failed and cleans partial vectors/chunks. A failed record remains deletable even if cleanup fails. A process lock prevents startup recovery from touching another live process's uploads; only one API or CLI instance may own a data directory. Re-uploading creates a new record. Background jobs are not required for this local MVP.

SQLite determines which files are eligible for retrieval. Only chunks belonging to `ready` files can become answer evidence. During deletion, first make the file ineligible, then remove its vectors, chunks, and file record, plus any optional original TXT copy. Report success only after cleanup completes; failed cleanup must remain retryable. SQLite and Chroma do not share a transaction, so eligibility checks and cleanup tests are required.

Retained messages are conversation context only. New answers must retrieve current evidence and must not reuse deleted excerpts as factual support.

### Question Answering

1. Accept the question and conversation ID. Load the relevant recent conversation history.
2. Resolve follow-up references into a standalone retrieval question when needed. History helps interpret the question but is not a factual source.
3. Embed the resolved question and retrieve the top K eligible chunks across available materials.
4. Provide those excerpts to the LLM with instructions to answer from evidence, preserve explicit academic years and semesters, identify conflicts, and state when information is insufficient.
5. Stream the answer and return source records and debug information. Validate that referenced source IDs belong to the retrieved evidence and resolve excerpts from stored source text.
6. Save the completed exchange. Keep failed or interrupted responses distinguishable from completed answers.

Do not infer a rule's effective date from its upload time. An empty retrieval result should produce an explicit insufficient-evidence response. For nonempty results, similarity alone does not establish whether the question is answerable; evidence handling must also be evaluated. Source-ID validation prevents invalid references but does not prove that the answer is supported by those sources.

### Frontend and Streaming

Use one page with a file sidebar and a primary chat area. Show upload progress and processing states, expandable source excerpts under each answer, and a lightweight debug panel containing retrieved chunks, the retrieval metric and scores, and processing time. Scores must not be presented as correctness probabilities.

The [MVP frontend design](mvp-frontend-design.md) specifies the reference-inspired Library, chat, and Evidence layout, responsive behavior, component responsibilities, and proposed API contracts. Sources remain expandable beneath each answer and are synchronized with the Evidence panel.

Use `fetch` for ordinary API calls and a streamed POST response with the `text/event-stream` content type for chat. Parse SSE frames incrementally because network reads may split an event or contain multiple events. Define typed events for answer deltas, sources, debug information, completion, and errors. A completion event marks a successful answer; a closed connection without it is an interrupted response.

Use React state and reducers for pending, streaming, completed, and failed states. A dedicated global state library is unnecessary for the current scope.

## LangGraph Position

LangGraph is optional, not a required MVP dependency. The initial workflow is short and mostly fixed, so ordinary Python functions provide a readable baseline.

If learning LangGraph becomes an immediate priority, the same functions can be wrapped in a small StateGraph without changing the product scope. Each step does not need to become an autonomous agent. LangGraph becomes more useful when later versions introduce branching retrieval, question decomposition, bounded retry loops, or resumable workflows.

LangGraph does not replace the API server, databases, model providers, or retrieval evaluation.

## Replacing Storage Components

### Chroma to Qdrant or Milvus

Replace the vector storage implementation while retaining the application-facing insert, search, and delete operations. Recreate the index and reimport the materials; preserving existing vectors is not required.

Adapt database-specific identifiers, filters, distance metrics, and scores. Repeat retrieval and deletion tests and rerun the fixed evaluation set. Similar interfaces do not guarantee identical rankings or compatible thresholds. Choose a replacement based on measured workload needs rather than assuming every alternative is faster.

### SQLite to PostgreSQL

SQLite is the database engine; SQLAlchemy is the Python library used to access it. SQLAlchemy can also access PostgreSQL, reducing database-specific code in the services.

Keep database access in a small storage module, use portable types and queries where practical, and avoid SQLite-specific SQL in business logic. To switch, configure the PostgreSQL driver and connection, create fresh tables, adapt any dialect-specific behavior, and rerun storage and API tests. Existing data can be discarded.

SQLAlchemy is not a guarantee that every query or transaction behaves identically across databases. Alembic can be introduced later if preserving data through schema changes becomes a requirement.

## Verification and Evaluation

| Area | Required coverage |
| --- | --- |
| Upload and chunking | Invalid formats, invalid UTF-8, empty text, chunk boundaries, source offsets, and processing failures |
| Retrieval and storage | Expected evidence, ready-file eligibility, failed writes, and source associations |
| Deletion | Complete cleanup, retry after partial failure, and exclusion from subsequent questions and follow-ups |
| Answer behavior | Supported answers, follow-up resolution, insufficient evidence, conflicting sources, and explicit year or semester handling |
| API and frontend | Upload states, source expansion, fragmented SSE events, completion, and interrupted or failed responses |

Use mock LLM and embedding implementations for deterministic automated tests. Maintain a fixed evaluation set covering the scenarios in the product design, with expected evidence and key answer points. Measure evidence retrieval separately from answer support, and record latency, model configuration, chunking settings, and retrieval settings with each run.

Before delivering the implemented MVP, verify the complete upload-to-answer workflow with real embedding and LLM providers. Mock tests alone do not establish real retrieval or answer quality.

For documentation-only changes, review the content, verify local links, and check formatting with `git diff --check`; automated documentation tests are not required. Application tests and live-provider checks apply when the corresponding implementation exists.

## Development and Later Iterations

During development, run Vite and FastAPI separately and proxy API requests through Vite. Keep SQLite, Chroma persistence, and uploaded source files in local data directories outside version control. `make app` builds the frontend and serves its assets and API under one local origin. For a hosted deployment, use one backend instance with persistent storage and review access control before exposing the server. Multiple backend instances require a separate storage and job-execution review.

Follow the product roadmap: Markdown and PDF parsing in V2, hybrid retrieval and reranking in V3, and need-driven agent capabilities in V4. OCR, knowledge graphs, long-term user memory, study planning, automatic web updates, and multi-user permissions remain outside the MVP.
