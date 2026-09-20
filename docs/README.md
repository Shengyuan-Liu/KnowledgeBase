# Documentation

## Project Organization

- [Project structure and module management](project-structure.md): the implemented directory layout, module responsibilities, shared initialization, and development workflow.

## Implemented Components

- [Frontend workspace](frontend.md): file management, streaming chat, citation navigation, conversation restoration, and offline browser acceptance tests.
- [File management API](file-api.md): FastAPI startup, TXT upload/list/delete endpoints, HTTP errors, and lifecycle tests.
- [Chat API](chat-api.md): complete JSON answers, continued conversations, source and citation fields, HTTP errors, and integration tests.
- [Streaming chat API](chat-streaming.md): incremental SSE text, request identity, completion, cancellation, and atomic answer persistence.
- [Conversation reading API](conversation-api.md): ordered history, saved evidence, legacy message compatibility, and deleted-file markers.
- [Embedding provider](embeddings.md): OpenAI integration, input and output contracts, local usage, and deterministic tests.
- [Vector database](vectordb.md): Chroma storage, search, file-scoped deletion, and local persistence tests.
- [Retrieval](retrieval.md): ready-file filtering, question embedding, vector search, and canonical chunk text.
- [File ingestion](file-ingestion.md): TXT validation, chunking, indexing, file states, and failure cleanup.
- [File deletion](file-deletion.md): retrieval exclusion, vector/chunk/file cleanup, transaction boundaries, and explicit retries.
- [Conversation storage](conversation-storage.md): conversation metadata, ordered message history, recent-message reads, and caller-owned transactions.
- [Conversation chat](conversation-chat.md): follow-up resolution, fresh retrieval, completed-turn persistence, and CLI resumption.
- [Citation checks](citations.md): source-number validation, returned diagnostics, and evaluation recording.

## MVP Design

All MVP specifications and their diagram assets live in `mvp/`.

1. [Product design](mvp/mvp-product-design.md): scope, user workflows, acceptance scenarios, and future iterations.
2. [Technical plan](mvp/mvp-technical-plan.md): stack, ingestion, retrieval, storage, streaming, and verification.
3. [Frontend design](mvp/mvp-frontend-design.md): layout, components, interaction states, and API contracts.
4. [System design](mvp/mvp-system-design.md): architecture and workflows, with a preview image and editable Excalidraw source.

These documents describe the intended application. They are not evidence that the implementation or its acceptance checks are complete.
