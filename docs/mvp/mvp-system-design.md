# MVP System Design Diagram

![Implemented KnowledgeBase components, ingestion and retrieval, question answering, file lifecycle, data storage, frontend streaming, and runtime](mvp-system-design.png)

Open [the editable Excalidraw diagram](mvp-system-design.excalidraw) using **Open** in [Excalidraw](https://excalidraw.com/). Use **Zoom to fit** for orientation, then zoom into one numbered section. The [SVG preview](mvp-system-design.svg) stays sharp at any zoom; the PNG is 5000 × 3420 pixels.

This map describes the implemented local MVP at commit `abd2e47`, reviewed on September 21, 2026 (UTC). It continues the original Chrome ingestion/retrieval sketch, preserving its 79 drawing elements in section 02. The surrounding sections explain the running application rather than future architecture. The diagram contains 40 component and workflow cards, with 260 editable elements overall.

## Reading the map

| Section | What it explains |
| --- | --- |
| 01 — System at a glance | React workspace → FastAPI routes → Python services → provider adapters → external OpenAI APIs, plus local storage and entry points. |
| 02 — Ingestion + retrieval data | Original TXT → chunks → embeddings → Chroma; query → vector search → chunk IDs → SQLite text. |
| 03 — One question → one saved answer | Original question, recent history, reference resolution, eligible retrieval, prompt construction, generation, citation checks, and atomic persistence before completion. |
| 04 — File lifecycle | Synchronous upload, processing and ready states, failed indexing, deletion, and restart recovery. |
| 05 — What is stored where? | SQLite tables and relationships, evidence snapshots, Chroma metadata, and retention of original text as chunks. |
| 06 — Frontend + stream contract | UI components and hooks, API clients, SSE events, source inspection, Stop, history restoration, and interrupted requests. |
| 07 — Startup, CLI + evaluation | Configuration, resource ownership, one data-directory owner, local servers, CLI, evaluation, and evidence limits. |

Read section 01 first. Follow 02 and 04 for an uploaded document, then 03 and 06 for a question. Use 05 to understand persistence and 07 to understand how the application starts and is checked.

Blue denotes browser/API/retrieval components; orange denotes ingestion and orchestration; green denotes durable state; purple denotes model calls and streaming; red denotes failure or deletion. Solid arrows show primary request/data direction. Dashed arrows show returned data. Storage reads return through the same adapters. Boxes inside the local application represent modules, not separately deployed servers.

## Implementation references

- [React workspace](../../frontend/src/Workspace.tsx), [library hook](../../frontend/src/hooks/useLibrary.ts), [chat hook](../../frontend/src/hooks/useChat.ts), and [chat state reducer](../../frontend/src/hooks/chatState.ts).
- [FastAPI application and lifespan](../../knowledgebase/api/app.py), [file routes](../../knowledgebase/api/files.py), [chat routes](../../knowledgebase/api/chat.py), [conversation history](../../knowledgebase/api/conversations.py), and [SSE encoding](../../knowledgebase/api/streaming.py).
- [File lifecycle service](../../knowledgebase/services/files.py) and [chat service](../../knowledgebase/services/chat.py).
- [Chunking](../../knowledgebase/rag/chunking.py), [reference resolution](../../knowledgebase/rag/query.py), [retrieval](../../knowledgebase/rag/retrieval.py), [context](../../knowledgebase/rag/context.py), [generation](../../knowledgebase/rag/generation.py), and [citation checks](../../knowledgebase/rag/citations.py).
- [Embedding adapter](../../knowledgebase/providers/embeddings.py), [language-model adapters](../../knowledgebase/providers/llm.py), and [configuration](../../knowledgebase/config.py).
- [SQLite initialization](../../knowledgebase/storage/database.py), [models](../../knowledgebase/storage/models.py), [operations](../../knowledgebase/storage/operations.py), [Chroma adapter](../../knowledgebase/storage/vectordb.py), and [storage ownership](../../knowledgebase/storage/runtime.py).
- [CLI](../../knowledgebase/cli.py), [local commands](../../Makefile), [evaluation runner](../../evals/evaluate.py), and [MVP release evaluation](../../evals/analyses/2026-09-21-mvp-release.md).

## Important boundaries

Only ready files supply current retrieval evidence. SQLite and Chroma do not share a transaction; file states and cleanup ordering control eligibility. Upload waits for indexing inside the request. There is no background worker, and original TXT content is stored as SQLite chunks rather than separate raw-file copies.

History helps resolve references but is not factual evidence. Citation-ID checks establish membership in the retrieved source list, not whether an answer is supported. Saved evidence snapshots survive source-file deletion. Retrieval distance is not a correctness probability. When retrieval returns no excerpts, the service supplies an insufficient-evidence response without calling answer generation.

A successful answer is committed before the stream emits `complete`. An early EOF is an interruption. A disconnect after commit can prevent completion delivery even though an answer was saved; existing conversations can be reloaded before retrying. The release evaluation records known quality limitations; this diagram is not test or answer-quality evidence.

## Editing and regeneration

The Excalidraw file is editable directly. The checked-in [layout generator](diagram/build-system-design.mjs) also produces the Excalidraw file, SVG, and component bounds from a readable layout definition. Its [original sketch data](diagram/original-ingestion-layout.json) preserves the observed geometry and text of the initial Chrome diagram.

To regenerate the documentation artifacts from the repository root:

```sh
node docs/mvp/diagram/build-system-design.mjs
rsvg-convert -o docs/mvp/mvp-system-design.png docs/mvp/mvp-system-design.svg
```

PNG rendering requires `rsvg-convert`. Regeneration overwrites the scene and previews; first save a separate copy of any manual Excalidraw edits that should be retained. After editing the layout, inspect both the rendered preview and the actual Excalidraw canvas for clipped text, missing shapes, or misleading arrows.
