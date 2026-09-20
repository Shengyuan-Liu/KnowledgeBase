# Documentation

## Project Organization

- [Project structure and module management](project-structure.md): the proposed directory tree, module responsibilities, dependency boundaries, development workflow, and implementation order.

## Implemented Components

- [Embedding provider](embeddings.md): OpenAI integration, input and output contracts, local usage, and deterministic tests.
- [Vector database](vectordb.md): Chroma storage, search, file-scoped deletion, and local persistence tests.
- [Retrieval](retrieval.md): ready-file filtering, question embedding, vector search, and canonical chunk text.
- [File ingestion](file-ingestion.md): TXT validation, chunking, indexing, file states, and failure cleanup.
- [File deletion](file-deletion.md): retrieval exclusion, vector/chunk/file cleanup, transaction boundaries, and explicit retries.
- [Original text storage](file-store.md): optional TXT storage utility; not used by the current ingestion workflow.

## MVP Design

All MVP specifications and their diagram assets live in `mvp/`.

1. [Product design](mvp/mvp-product-design.md): scope, user workflows, acceptance scenarios, and future iterations.
2. [Technical plan](mvp/mvp-technical-plan.md): stack, ingestion, retrieval, storage, streaming, and verification.
3. [Frontend design](mvp/mvp-frontend-design.md): layout, components, interaction states, and API contracts.
4. [System design](mvp/mvp-system-design.md): architecture and workflows, with a preview image and editable Excalidraw source.

These documents describe the intended application. They are not evidence that the implementation or its acceptance checks are complete.
