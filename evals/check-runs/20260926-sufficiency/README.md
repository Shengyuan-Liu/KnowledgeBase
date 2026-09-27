# Evidence sufficiency verification

Date: 2026-09-26. Branch: `v2`; base commit `d353933`. Each command JSON retains
its command, base commit, source hashes, device, duration, counts, output and full
metric inventory. No paid provider calls, live judge, full live RAG evaluation,
production-data mutation, acceptance or merge occurred. Local `.env` is unchanged.

## Checks and retained failures

| Record | Result | Scope |
| --- | --- | --- |
| `focused-1` | 62 passed, 1 failed | New assessment and existing planning suites; test incorrectly assumed ordering among equal-ranked synthetic files |
| `focused-2` | 63 passed | Corrected source-membership assertion; ranking ties remain governed by existing merge behavior |
| `backend-1` | 9 collection errors | Command omitted `tests`; pytest collected archived evaluation scripts with duplicate module names, before executing tests |
| `backend-2`, `backend-3` | 705 passed, 1 skipped each | Full offline suite, before/after isolating assessment-only answer instructions and pending-node metadata |
| `final-focused-1` | 56 passed | Final assessment, dependency and generation checks, including early completion of a whole dependency chain |
| `backend-4` | 706 passed, 1 skipped | Final full offline suite |
| `frontend-1`, `frontend-2` | 46 passed each | UI/transport unit tests, including four assessment labels and older saved plans |
| `build-1`, `build-2` | Passed | TypeScript and production builds |
| `browser-1` | 20 passed, 1 failed | Planned PDF fixture still returned library requirements, causing abstention instead of the citation button assumed by its viewer test |
| `browser-2` | 1 passed, 1 failed | PDF-specific assessment correctly found no retained sales value in the mock-vector context; viewer test still assumed a cited answer |
| `browser-3` | 21 passed | Full browser suite using the always-available View evidence action for PDF navigation, including abstention |
| `browser-4` | 4 passed | Final desktop/mobile assessment display, reload and cancellation after singular/plural copy fix |
| `comparison-1`, `comparison-2` | Passed | Frozen before/after controller replays; second uses final assessment-only prompt separation |
| `measurements-1` | Passed | Full comparison inventories and local timing summaries |
| `docs-1`, `docs-2` | Passed | English content, local links, fences, source whitespace and record review |

Failed outputs and browser traces remain append-only. The generic record runner
counts singular `error`, so `backend-1.json` understates collection errors; the
explicit correction in [measurement-supplement.json](measurement-supplement.json)
and its raw log retain all nine. Subsequent backend commands target `tests` and
never collect historical acceptance scripts. No live test was executed.

The browser failures required fixture/test corrections, not a fallback answer.
Mock PDF retrieval does not necessarily retain the requested sales cell, and the
assessor now exposes that gap. Original-page navigation must work even when the
answer abstains; the final browser check exercises that path. Existing test
fixtures intentionally remain unsuitable for measuring answer correctness.

Known warnings remain: Starlette BlockingPortal deprecation, Docling OCR option
deprecation and browser NO_COLOR/FORCE_COLOR environment warnings. The single
backend skip is the opt-in live API test. No unresolved product failure remains
in the exercised offline scope. Live assessment semantics remain unverified.

## Coverage and review

Real SQLite/Chroma, service and HTTP checks cover one-pass support, three-round
source-bound gap search, four statuses, exact references, schema/requirement ID
validation, invented evidence rejection without repair, direct-route candidate
merging, all-missing abstention without generation, duplicate/no-progress stops,
shared six-query and three-round limits, explicit file scope, source deletion,
revoked earlier support, empty-budget behavior and PDF supplement offsets.
A real SDK with an offline HTTP transport verifies the strict schema and request
caps. Cancellation/timeout during assessment produces no later source event,
answer or saved exchange. JSON/SSE/history retain the same final context and
assessment, including historical source deletion. Original stage 3 suites run
with sufficiency disabled to preserve their isolated contract coverage.

Codex inspected the 390px and 1440px evidence screenshots: statuses, gaps, quotes
and filenames fit the existing scrollable panel. The first screenshot exposed
“1 retrieval rounds”; the final scoped browser run records corrected copy.
This is model visual review, not independent human acceptance. Browser answers
are fixtures and are not graded for completeness or citation support.

## Frozen comparison

[fixture.json](fixture.json) fixes four canonical documents, complete binary span
labels, six questions/scopes/budgets, query vectors and point definitions. Initial
plans and frozen assessment decisions are constructed deterministically from that
fixture. The control disables `PlanningOptions.sufficiency_enabled`; the after
variant enables it. All other settings are identical: vector strategy, per-query
candidate limit 1, final K=3, no reranker, and 4096 evidence tokens (1 in the budget
case). Both variants use current code, not different binaries or live models.

[comparison-2-details.json](comparison-2-details.json) retains twelve exchanges,
exact model inputs and outputs, candidate ranks, final source text, source quotes,
proposals/exclusions, per-round context, token budgets, stop reasons and per-case
deltas. The earlier replay is preserved in `comparison-1-details.json`.

| Variant | Recall@3 | Precision@3 | Hit Rate@3 | MRR@3 | NDCG@3 | Final span coverage |
| --- | --- | --- | --- | --- | --- | --- |
| Before | .800000 | .400000 | 1 | 1 | .845259 | .700000 |
| After | .900000 | .466667 | 1 | 1 | .922629 | .800000 |

These are macro means over five cases with gold spans. The unanswerable case has
no relevance denominator and is excluded, never zero-filled. Candidate metrics
measure selected order before packing, use K as the precision denominator even
when fewer hits are present, and use binary NDCG gain with log2 discount. MRR is
cut off at K. Final coverage separately requires complete annotated spans in the
actual answer context. Query-level and reranking quality are not scored.

Codex reviewed all six pairs against the frozen canonical texts:

- Fill gap: the initial context contains closing hours; the supplementary access
  query adds the card rule. Final span coverage rises from 1/2 to 1.
- Already supported: one query and one assessment suffice; no extra search runs.
- Conflict: both incompatible closing times remain, with two source references
  and an unresolved conflict label. No invented resolution is added by control.
- Unanswerable: irrelevant chair text remains visible; the all-missing decision
  returns the standard abstention without calling the answer model.
- Scope limited: the excluded access document is never searched. The remaining
  access gap survives a no-progress stop; allowed-span coverage stays 1.
- Budget exhausted: both variants supply no text. The after variant marks both
  points missing without calling the assessor. Candidate hits do not imply support.

No case loses final gold-span coverage. The improvement is deliberately exposed
by synthetic vectors and fixture decisions; it does not establish model quality,
real-world retrieval gains, correct conflict assessment or abstention rates.

## Measurement boundaries

[measurement-supplement.json](measurement-supplement.json) supplies the full metric
inventory for both replays, overriding generic offline-check statuses where the
comparison actually measures retrieval, local latency and execution reliability.
It records package versions, sample counts, mean/P50/P95 and the nearest-rank
percentile method. Requests run sequentially at concurrency 1, without model
loading or provider queues; cold tokenizer effects may affect the first control.

Complete-response timing here is synchronous service entry through completed
exchange persistence, not HTTP or live-model latency. Retrieval, planning and
assessment timings are local diagnostics; component details remain in the raw
traces. Streaming first-answer-delta latency is not measured by this synchronous
comparison. Throughput/load behavior is unavailable. No usage or billing is
inferred from local input/evidence token counts. Whole-turn live cost is unmeasured.

Answer correctness, faithfulness, completeness, relevance, citation support and
coverage, and semantic appropriate/incorrect abstention are not scored for mock
answers. Frozen assessment labels are not model judgments or ground truth for
future live outputs. A separate live acceptance run must measure those dimensions,
false sufficiency, unnecessary searches and representative failure cases. Existing
PDF extraction limits remain; this change adds no parser-fidelity measurement.
