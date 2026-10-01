# Automatic planning / chat integration verification

Date: 2026-09-26. Branch: `v2`; base `ed05cf9`. Each command JSON retains the base
commit, exact tracked/untracked source hashes, command, device, duration, exit
status, counts and the complete metric inventory. No live provider, paid judge,
full RAG evaluation, production data modification or acceptance/merge was performed.
Credentials and `.env` were not changed. Mock keys only appear in offline fixtures.

## Scope and results

| Record | Result | Scope |
| --- | --- | --- |
| `regression-1` | 104 passed | Existing providers, chat/API/SSE/config and executor contracts |
| `planning-1` | 17 passed | Structured planner, invalid plans, scope, persistence, follow-ups and cancellation |
| `planning-2` | 21 passed | Adds deadlines, stalled final stream closure and actual SDK zero-retry behavior |
| `backend-1` | Collection failed: 9 errors | Unrestricted pytest discovered duplicate module names in archived evaluation scripts; no tests ran |
| `backend-2` | 659 passed, 1 skipped | Correct project suite `pytest tests -q`, matching Makefile scope; live API test skipped |
| `frontend-1`, `frontend-2` | 44 passed each | Existing UI/SSE state and transport tests, including updated request contract |
| `browser-1` | 3 passed | New desktop/mobile plan display, history restore and cancellation |
| `browser-2` | 17 passed | Complete offline browser suite, including PDF in single and planned mode |
| `browser-3` | 5 passed | Planning/PDF after moving plan into the scrolling evidence body |
| `build-1` | Passed | Initial TypeScript and production build |
| `build-2` | Failed | New browser test had an unused `request` fixture parameter |
| `build-3`, `build-4` | Passed | Removed unused parameter; final UI layout builds |
| `comparison-1` | Failed | Replay runner used text-only history API, which has no retrieval field |
| `comparison-2` | Failed | Runner compared a typed history model against a JSON dict |
| `comparison-3` | Passed | Correct display-history API and typed comparison; all frozen retrieval metrics match stage 3a |
| `docs-1` | See retained record | Content, links, code fences, English prose and whitespace review |

Failed logs and records are retained unchanged. Runner errors were fixed in the
runner, not hidden by product fallbacks. Known warnings: Starlette BlockingPortal
alias deprecation, Docling OCR configuration deprecation, and browser NO_COLOR /
FORCE_COLOR environment warning. No unresolved product failure was found in this
scope. Live planning quality, real latency and whole-turn cost remain unmeasured.

Backend checks use offline provider stubs and HTTP MockTransport with real SDK
serialization/stream parsing, real SQLite/Chroma and isolated temporary data. The
new API/CLI tests exercise configured/overridden modes. Cancellation and deadlines
cover planning, query execution and final streaming; later work does not persist a
successful exchange. Scope tests include an unresolved PDF reference. Browser tests
use real HTTP/storage, fixed embeddings/plans/answers and cached PDF extraction.
They verify integration and page navigation, not new PDF extraction quality.

`browser-*-artifacts/` retains screenshots from each browser invocation. Codex
visually inspected desktop/mobile plan panels and checked spacing, wrapping,
scrolling and citation access. The plan was moved into the same padded scroll body
as source excerpts after the first inspection. This is model visual review, not
human acceptance. PDF page rendering/reload/deletion assertions passed in both modes.

## Frozen paired replay

[compare.py](compare.py) reuses the byte-identical
[stage 3a fixture](../20260926-planned-retrieval/fixture.json): four source spans,
four cases (direct, independent, duplicate, exhausted budget), two retrieval
strategies, two variants. K=2, complete binary span labels, fixed vectors, shared
index and settings. Candidate metrics use selected child order before packing;
final coverage uses entire gold source spans present in actual context. Per-query
candidate diagnostics and budget exclusions remain in the retained plan trace.
This fixture does not exercise reranking, dependency queries or live models.

The new planned route goes through PlannerClient validation and the chat service
with a frozen mock model decision, final-answer placeholder and saved history.
The single variant uses the existing service path. All 16 completed exchanges,
model inputs, plan outputs, source text, ranks, context, settings and per-case
metric deltas are in [comparison-3-details.json](comparison-3-details.json).
The fixture hash and assertion against the previous aggregate are also retained.

| Strategy | Variant | Recall@2 | Precision@2 | Hit Rate@2 | MRR@2 | NDCG@2 | Final span coverage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Vector | Single | .75 | .50 | 1 | 1 | .806574 | .625 |
| Vector | Planned | 1 | .75 | 1 | 1 | 1 | .75 |
| Hybrid | Single | 1 | .75 | 1 | 1 | 1 | .75 |
| Hybrid | Planned | 1 | .75 | 1 | 1 | 1 | .75 |

The vector independent case gains one missing fact. Hybrid already supplies both
facts and gains nothing. The one-token case still excludes all evidence in both
variants; better candidates cannot overcome that budget. Direct/duplicate cases
remain unchanged. Codex reviewed all eight pairs from the trace and deterministic
source-span labels; no semantic answer assessment or human reviewer was used.
These hand-authored plans/vectors intentionally expose mechanisms and cannot show
that a live planner will improve answers. No live quality improvement is claimed.

## Measurement boundaries

[measurement-supplement.json](measurement-supplement.json) overrides the generic
comparison-3 metric inventory with measured fixture values and stage timing summaries.
Other command records describe offline test scope. Raw mocked durations are not
production latency. Resolver/embedding/final-model usage is unavailable in the
new trace; planner usage is saved only if returned. Actual billed cost is not inferred.
A future live acceptance run must instrument whole-turn usage and answers before
making quality/cost/performance claims.

The replay is sequential (concurrency 1), with no model loading or provider queue.
The tokenizer may be cold on the first pair; the baseline runs first. Timings include
in-process SDK mocks and local storage; separate affected-stage and service summaries
are diagnostics only. There is no streaming latency observation in this replay.
Browser/test durations are not time to first answer delta. Ingestion/index performance
is not benchmarked; lifecycle behavior is covered by contract/browser assertions.
