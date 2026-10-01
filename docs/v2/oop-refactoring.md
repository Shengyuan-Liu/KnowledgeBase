# Object Oriented Refactoring Plan

This document specifies the behavior-preserving OOP refactor authorized on
2026-10-01. It is the implementation guide and progress record for subsequent
work on `v2`. The baseline is commit `bbd0a8d`. Implementation authorization does
not authorize merging this work into `main`.

The objective is to put stable dependencies and configuration in cohesive objects,
keep each request's mutable state separate, and make API, CLI and evaluation
callers use the same components. Retrieval quality, algorithms, prompts, storage
formats, defaults and public HTTP contracts are not intentionally changed.

## Architecture

```text
API / CLI
  FileService -> DocumentParser -> LocalPdfParser -> PdfParser
              -> DocumentChunker -> splitting algorithms
              -> EmbeddingClient / SQLite / ChromaStore / PdfAssets
  ChatService -> RagClient -> Retriever -> Reranker -> RerankerClient
                          -> PlannerClient
                          -> HopController -> Retriever / PlannerClient
                          -> LLMClient / StreamingLLMClient
Evaluation -> RagClient or ChatService, with isolated storage and explicit settings
```

Construct components at the application boundary. Components receive dependencies
explicitly and do not read `.env`, open a second application runtime, or construct
SDK clients internally. Prefer composition; no generic base-class hierarchy,
dependency-injection framework, plugin registry or repository framework is needed.

## New component classes

| Class | Responsibilities | Main interface | Stable dependencies |
| --- | --- | --- | --- |
| `Retriever` | Resolve eligible file scope; retrieve candidates; coordinate vector/BM25/RRF/reranking; execute supplied query plans; expand and pack evidence | `retrieve`, `retrieve_candidates`, `retrieve_plan`, `pack` | Session factory, embeddings, Chroma store, optional reranker, retrieval settings |
| `Reranker` | Bound candidate window and input budget; score, sort and retain ranking diagnostics | `rerank` | Reranker client, candidate/input limits, tokenizer |
| `RagClient` | Prepare plans; coordinate single/planned/multi-hop evidence; build answer sources; generate complete or streamed answers; check citation IDs | `answer`, `stream`; private planning, evidence and source assembly methods | Retriever, sync/streaming LLM clients, optional planner, planning options |
| `ChatService` | Read conversation history; resolve follow-ups; call RAG; persist completed exchanges; read saved conversations | `answer`, `stream`, `get_conversation`; private history/persistence methods | Session factory, RagClient, resolver LLM, history limit |

`Retriever.retrieve_plan` executes the supplied query batch and packs its merged
results. It does not decide whether to run another round. `HopController` owns
that decision and its associated progress. `RagClient` coordinates an answer;
`ChatService` owns conversation persistence. `RerankerClient` executes a model;
`Reranker` owns the application ranking policy.

Constructor arguments hold reusable dependencies and default settings. Method
arguments hold question text, selected file IDs, per-operation limits, request
control and explicit plan/run data. Defaults may be overridden for the existing
planned-retrieval candidate budgets without mutating shared configuration.

## Existing classes to reorganize

| Class | Destination and changes |
| --- | --- |
| `DocumentParser` | Move from `services/files.py` to `rag/parsing.py`; keep `prepare` and `parse` with existing validation and source identity behavior |
| `DocumentChunker` | Move from `services/files.py` to `rag/chunking.py`; own splitting configuration and optional semantic embedding dependency; retain `split` |
| `FileService` | Keep ingestion/deletion/recovery transactions; inject parser and chunker; add file list/detail/original-source reads currently embedded in routes |
| `LocalPdfParser` | Move the lazy runtime wrapper to `rag/pdf_runtime.py`; preserve optional dependency loading and sequential conversion |
| `PdfParser` | Keep concrete extraction, model identity and page/table mapping in `rag/pdf.py` |
| `HopController` | Receive Retriever instead of repeating storage/model/retrieval parameters; preserve per-request rounds, bindings, assessment and stopping rules |
| `RequestControl` | Keep a fresh deadline and cancellation signal per planned request; preserve the final-generation reserve and bounded provider calls |
| `AppResources` | Move out of FastAPI dependencies to a framework-independent bootstrap module; hold assembled services as stable instances |

`FileService` exposes `ingest`, `delete`, `recover`, `list_files`, `get_file` and
`get_original`. Original-source lookup returns file/path information; HTTP
responses and HTTP error translation remain in the route layer. Keep existing
status codes, messages, revision checks and deletion behavior.

## Existing supporting classes

These classes retain their purpose; update imports and consumers as needed.

| Class | Responsibilities and methods |
| --- | --- |
| `EmbeddingClient` | `embed_documents`, `embed_query`, `bounded` |
| `LLMClient` | Synchronous `generate` and request-specific `bounded` copies |
| `StreamingLLMClient` | Asynchronous `stream`, stream cleanup and `bounded` copies |
| `PlannerClient` | `plan` and structured model calls for planning, binding and assessment |
| `RerankerClient` | Model/device/batch/tokenizer ownership and serialized `score` |
| `GenerationLimits` | Per-generation input/output/time budgets and `check_input` |
| `ChromaStore` | Vector `upsert_chunks`, `search`, `delete_by_file_id` |
| `PdfAssets` | Original PDF `save`, `path`, `delete` |
| `Settings` | Entry-point environment configuration |
| `RetrievalOptions` | Retrieval strategy, fusion, reranking and packing settings |
| `PlanningOptions` | Planning, round, assessment and request limits |
| `ChatStreamingResponse` | HTTP SSE framing, disconnect cancellation and iterator cleanup |

`PreparedPlanning` and `PlannerResult` remain data objects. Shared document,
retrieval, planning and chat schemas stay in `schemas`; ORM records stay in
`storage/models.py`. Do not duplicate them inside component modules or change
their serialized contracts as part of this refactor.

## Algorithms that remain functions

Keep input/output algorithms independently testable. The following functions have
an explicit component owner without requiring a separate wrapper class for each.

| Algorithm or helper | Component using it |
| --- | --- |
| TXT/Markdown parsing | DocumentParser |
| Character, structural, parent-child and semantic splitting | DocumentChunker |
| PDF heading/table context and source-location mapping | Parser/chunker/retrieval components |
| BM25 scoring and route/cross-query RRF | Retriever |
| Document scope interpretation | Retriever and plan preparation |
| Evidence token accounting and packing | Retriever |
| Follow-up resolution | ChatService |
| Context/prompt construction and grounded generation helpers | RagClient |
| Citation-number membership checks | RagClient |
| Literal binding validation, assessment reference validation and source-span progress | HopController |
| SQLite reads and writes | Owning service/component, using short-lived sessions |

Do not introduce BM25 caching, change corpus statistics, alter tokenizer behavior,
rewrite prompts, expand validation or add fallback/repair paths during migration.

## Resource and request lifetimes

- Share service objects, provider clients, loaded models, vector store and session
  factory for one application runtime. Shared configuration is treated as fixed.
- Create RequestControl and HopController for each request. Keep question text,
  history, evidence, answer parts, diagnostics and progress in request-local state.
- Request-bounded embedding/LLM dependencies are copies or explicit local inputs;
  never replace the shared client's limits with one request's deadline.
- Database sessions are short-lived. Conversation reads close before generation;
  a completed exchange is saved in the existing final transaction.
- Preserve streaming cancellation checkpoints, closing of provider iterators,
  progress/source/debug/complete/error event contracts and successful-only saves.
- Bootstrap owns SDK/storage lifetimes and invokes recovery while it owns the data
  directory lock. Storage initialization must not import FileService.
- Keep the local reranker lock and lazy PDF lock; these address observed runtime
  behavior and must not be removed as cosmetic cleanup.

## Module and call migration

The package remains `knowledgebase/`; keep the current `schemas`, `providers`,
`storage`, `rag`, `services` and `api` boundaries. New modules are
`knowledgebase/bootstrap.py`, `knowledgebase/services/rag.py` and
`knowledgebase/rag/pdf_runtime.py`.

| Current implementation | Target |
| --- | --- |
| `services.chat.answer_question` | `services.rag.RagClient.answer` |
| `services.chat.answer_in_conversation` | `services.chat.ChatService.answer` |
| `services.chat.stream_answer_in_conversation` | ChatService.stream for history/persistence plus RagClient.stream for RAG events |
| `services.chat._retrieve_evidence` | Retriever retrieval plus RagClient source/diagnostic assembly |
| `rag.retrieval.retrieve_evidence` | Retriever.retrieve |
| `rag.retrieval.retrieve_candidates` | Retriever.retrieve_candidates |
| `rag.planned_retrieval.retrieve_plan` | Retriever.retrieve_plan, retaining pure query-merging helpers |
| `rag.retrieval.pack_retrieval_candidates` | Retriever.pack |
| `rag.reranking.rerank` | Reranker.rerank |
| `services.planning.prepare_planning` | RagClient plan preparation |
| File/conversation reads inside routes | FileService and ChatService |
| `api.dependencies.AppResources` and repeated entry-point construction | bootstrap.AppResources and build_resources |

Migrate active API/CLI/evaluation scripts and tests to the new interfaces. Temporary
adapters may support individual migration commits, but remove superseded public
function entry points before delivery. Historical scripts under retained run
directories remain unchanged; replay them at their recorded revisions.

## Stages and acceptance gates

1. **Plan and baseline.** Commit this document first. Freeze representative offline
   input/output observations before production edits. Record baseline checks.
2. **Document processing.** Move parser/chunker/PDF wrapper classes, inject their
   dependencies, and verify source offsets, chunk IDs, budgets and file lifecycle.
3. **Reranking and retrieval.** Introduce Reranker and Retriever; migrate planned
   retrieval and HopController callers. Verify ranks, evidence text, exclusions,
   scope, parent/child behavior and retrieval diagnostics on the frozen workload.
4. **RAG and conversations.** Introduce RagClient and ChatService. Verify prompts,
   complete/streamed answer parity, history resolution, source snapshots, deadlines,
   cancellation and persistence. Exercise reuse across independent requests.
5. **Bootstrap and consumers.** Assemble stable services once; migrate API, CLI,
   active evaluation runners and test fixtures; move recovery to bootstrap.
6. **Closeout.** Remove obsolete adapters, update affected docs, run the applicable
   offline suite and controlled browser regressions, compare frozen observations,
   and record completion, deviations and remaining limitations here.

Make one corresponding Git commit for each completed stage, with its checks and
recorded failures. Keep intermediate stages reviewable; a stage is not complete
merely because files have been moved or an import compiles.

## Verification and measurement

Follow the [measurement policy](../../evals/measurement-policy.md). Store each
attempt under a new record in `evals/check-runs/20261001-oop-refactoring/`; retain
command, revision/working-tree identity, duration, pass/fail/skip/error counts and
raw output. Include the full metric inventory with measured, not_applicable or
unavailable status and a reason. Do not modify historical run artifacts.

Freeze deterministic offline questions, corpus, labels, provider responses and
settings for before/after observations. Compare chunks, ranked candidates, final
evidence, prompts, answers, citations, event order and persisted snapshots, ignoring
only explicitly documented nondeterministic IDs and timings. Record the comparison
scope and any difference; mocked equality is not a live answer-quality claim.

Run relevant unit/integration tests at each stage. At final integration, run the
backend suite and existing controlled browser regressions for affected API flows.
Add focused tests for shared-instance request isolation and component reuse.
Preserve existing real-problem regressions and avoid tests that only assert method
delegation. No new paid LLM calls or full live RAG evaluation are required for this
behavior-preserving refactor. Live quality, billing and production performance are
not applicable to mocked checks, or unavailable where no measurement exists.

Review documentation for content, relative links, English text and formatting.
Record documentation-only reviews in the commit message or a check record.

## Progress

- Plan: committed as `d5a1cde`.
- Baseline: 854 passed, 1 opt-in live test skipped. Frozen HTTP, prompt,
  schema and persisted-history observations are retained in
  [the check directory](../../evals/check-runs/20261001-oop-refactoring/README.md).
- Document processing: pending.
- Reranking and retrieval: pending.
- RAG and conversations: pending.
- Bootstrap and consumers: pending.
- Final verification: pending.
- Merge: not authorized.
