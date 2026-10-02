# Layered Architecture Verification

Date: 2026-10-01. Branch: `v2`. Starting revision: `3d7d7dd`.
Each command receipt records the starting commit, source hashes, exact command,
platform, elapsed time, counts, output and complete 20-item metric inventory.
The final implementation commit contains this directory and the recorded source.

## Result and comparison

The Python module graph is acyclic under explicit absolute, relative,
function-local, type-only and supported literal dynamic imports. It satisfies
the downward layer rules in [test_architecture.py](../../../tests/test_architecture.py).
The prior `chunking -> semantic_chunking -> chunking` cycle is removed. Runtime
Settings no longer sits beneath schemas, providers, storage, RAG or services.
RagClient and its planning/hop controller now belong to the reusable RAG layer.

The [architecture document](../../../docs/v2/layered-architecture.md) defines
component ownership, permitted dependencies, class APIs and standalone use.
`dependency-comparison-2.json` retains both graphs under the same new rules; the
before graph is read from `3d7d7dd` without running that application.
The scan includes 68 active Python modules, up from 64. Forbidden edges under
the explicit layer rules fall from 14 to zero; the resulting graph has no cycles.
Frontend source is unchanged from the previous successful
[frontend dependency audit](../20261001-dependency-audit/frontend-dependencies.json).

`behavior-before.json` and `behavior-after.json` preserve the same deterministic
offline fixture: questions, source text, model responses, configuration and
contracts. All 11 normalized observation groups, including nine schemas, are
identical. Normalization only removes recorded nondeterministic timing/identity
fields using the existing OOP fixture. This is contract preservation, not a live
quality comparison.

## Commands and outcomes

| Receipt | Scope | Outcome |
| --- | --- | --- |
| `before-contracts.json` | Frozen behavior at starting revision | 1 passed |
| `focused-1.json` | Architecture, configuration, parser/chunker integration, ingestion and frozen contract checks | 104 passed |
| `standalone-1.json` | First fresh-process examples | 2 passed, 4 failed: missing required chunk offsets and a generated-code string escaping error |
| `standalone-2.json` | Corrected examples | 5 passed, 1 failed: test accessed `RetrievedChunk.file_id` instead of `RetrievedChunk.chunk.file_id` |
| `architecture-1.json` | Layer rules, cycle detection, scanner regression and standalone examples | 10 passed |
| `lint-1.json` | Ruff syntax/undefined-name checks | Passed |
| `backend-final.json` | Complete backend suite including architecture and standalone tests | 868 passed, 1 opt-in live test skipped; pytest duration 38.09 seconds |
| `browser-final.json` | Real Playwright browser, offline provider fixtures, one worker | 21 passed; runner duration 37.6 seconds |
| `review-final.json` | Initial combined review | Graph, contract and link checks passed; example execution failed because the review script omitted the repository from its Python import path |
| `review-final-2.json` | Corrected review runner: graphs, contract equality, source scope, documentation/example review | Passed |
| `whitespace-final.json` | Git whitespace check | Passed |

The failed standalone attempts were errors in the new verification examples.
Their complete outputs remain retained. Correcting them required no further
application changes. The final suite includes all corrected cases.
The review-runner failure is retained with its original script in
`review_attempt1.py`; adding the repository to that runner's import path lets the
already verified standalone example execute. It is not a component dependency
on application startup.

## Standalone evidence

Six fresh-process cases install an import blocker before importing components.
Every case blocks `config`, `bootstrap`, API and CLI. Depending on the boundary,
it also blocks application services, RAG, storage or providers. Processes run
outside the repository in temporary directories without `.env` or OpenAI
environment variables. They exercise:

1. Pure schemas/options/defaults without runtime configuration or adapters.
2. Embedding and LLM clients with an injected fake SDK, without RAG or storage.
3. Markdown parsing, all four chunking modes and candidate reranking, without
   storage or services; PDF and torch imports are also blocked for this text path.
4. Real SQLite/Chroma creation, persistence across reopen, search and deletion,
   without providers, RAG or application services.
5. Retriever and RagClient against an explicit temporary index, without importing
   application services or web startup.
6. FileService ingestion and ChatService answer/history/deletion, without runtime
   configuration, bootstrap or transport entry points.

The backend suite also covers existing PDF, planned/multi-hop retrieval, scope,
reranking, deadlines, streaming cancellation and storage regressions. Browser
coverage includes upload, chat, multi-hop progress, PDF citations, history,
responsive layouts, cancellation and deletion using the real local API and
controlled model/PDF fixtures.

## Measurement scope and limits

Quality, live provider usage/cost, production latency, throughput and ingestion
performance metrics are `not_applicable` to these deterministic offline checks.
Per-command duration and pass/fail/skip counts are recorded separately; suite
duration is not answer latency. Actual temporary storage behavior is checked for
correctness without claiming a storage performance benchmark. No paid provider
call, full RAG evaluation or live judge calibration was run.

The static graph covers explicit source imports rather than arbitrary reflection
or third-party internals. Fresh-process execution checks transitive package
initialization for the exercised paths. Independent installation of different
distributions is not claimed; components still use this project's environment
and any dependencies required by the operation.

Existing Starlette/Docling deprecation and Node color-environment warnings remain
visible in the final logs. The previously observed generic-source phrase failure
(`my uploaded documents`) is unchanged; this refactor does not repair source
resolution or claim that all product defects are gone. There is no database
migration, reindexing requirement, frontend source change or authorized merge.

Documentation was reviewed for current module names, responsibilities, English
text, working relative links and balanced code fences. The documented standalone
chunking example is executed by `review.py`. The requested tutorial and upstream
manifest references were opened during the implementation's design review.
