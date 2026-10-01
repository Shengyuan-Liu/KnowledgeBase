# Evidence-dependent retrieval verification

Date: 2026-09-26. Branch: `v2`; base `b889c99`. Command JSON files preserve exact
commands, base commit, source hashes, device, duration, exit status, counts and the
complete metric inventory. The source hashes distinguish intermediate revisions.
All checks use isolated local data and mocked providers. No paid calls, live judge,
full live RAG evaluation, production-library changes, acceptance or merge occurred.
The existing key authorization remains valid; this work did not modify `.env`.

## Checks and retained failures

| Record | Result | Scope |
| --- | --- | --- |
| `regression-1` | 44 passed | Existing independent planning/executor contracts after graph/schema extension |
| `hops-1` | 13 failed, 2 passed | Fixture error: upload embeddings still used inherited 2D side effect while query vectors were 3D |
| `hops-2` | 1 failed | Direct-service diagnostic exposed the actual Chroma dimension mismatch |
| `hops-3` | 16 passed | Corrected fixture; multi-hop/API/SSE/provenance/scope/deletion/limits/cancellation tests |
| `backend-1` | 677 passed, 1 skipped | Full offline Python suite, including batching and cross-round deduplication |
| `focused-1` | 49 passed | Dependency/executor/CLI checks, with PDF supplement reference coverage |
| `focused-2` | 62 passed | All planning contracts after source-name provenance and all-prerequisite eligibility |
| `backend-2` | 678 passed, 1 skipped | Final full offline suite; live API test intentionally skipped |
| `frontend-1` | 44 passed | UI state and transport unit tests |
| `build-1`, `build-2` | Passed | TypeScript and production build, including final source-name display |
| `browser-1` | 2 failed, 1 passed | Fast successful responses completed before the test observed transient round-2 text; cancellation case passed |
| `browser-2` | 20 passed | Complete browser suite after removing timing-sensitive success-path assertion |
| `browser-3` | 3 passed | Final desktop/mobile dependency references and cancellation after source-name display |
| `comparison-1`, `comparison-2` | Passed | Frozen controller comparison before/after final provenance-label update |
| `docs-1`, `docs-3` | Passed | Content, English prose, local links, fences and source whitespace review |
| `docs-2` | Failed | Staged check included verbatim Playwright failure snapshots with trailing spaces; final check excludes only those raw artifacts and logs |

Raw failed logs and browser traces remain append-only. Playwright failure-source
snapshots retain their original trailing spaces; source/docs whitespace checks
exclude those raw snapshots alongside raw logs. Fixture dimensionality was
fixed by clearing its inherited embedding side effect; product embedding behavior
was unchanged. Progress ordering remains explicitly asserted at the SSE layer;
the browser cancellation fixture holds binding open and verifies round-2 progress.
Successful browser cases assert durable completed traces rather than requiring a
brief transient label to stay visible. There is no artificial product delay.

Known warnings remain: Starlette BlockingPortal deprecation, Docling OCR setting
deprecation, and browser NO_COLOR/FORCE_COLOR environment warnings. No product
failure remains in the exercised scope. Live model semantics and production
performance remain unverified.

## Coverage

Real SQLite/Chroma and HTTP API tests cover three-hop source binding, two ready
nodes sharing a structured call, exact source quotes and offsets, rejected invented
IDs/quotes/targets, schema/topology/query/round limits, missing/ambiguous targets,
Ready-only scope, deletion during binding, every prerequisite needing a retained
excerpt, canonical-span progress, cross-round query deduplication, cancellation,
timeouts and successful history persistence. No incomplete exchange is saved.

PDF regression checks retain the shared evidence token budget and verify that
binding references can point to separately located table supplements with canonical
offsets. This is not a new parser-quality evaluation. The full browser suite also
retains PDF page-navigation, Markdown, source scope and historical deletion checks.

`browser-*-artifacts/` retains failed traces and successful screenshots. Codex
visually inspected the 390px and 1440px dependency panels: target, supporting quote,
source filename and final sources fit in the evidence scroll area; restored history
shows the same plan. This is model visual review, not independent human acceptance.

## Frozen comparison

[fixture.json](fixture.json) freezes five source spans, complete binary labels,
query vectors, four questions/scopes/budgets and exact planner decisions. Each
pair uses the same corpus, labels, index, vector strategy, K=3, candidate limit=1,
4096-token budget (or 1 in the exhaustion case) and disabled reranker. A direct
query retains its existing top-k candidate path; each dependent query uses the
configured per-query limit before the shared final top-k selection.

The before variant replays the predecessor's direct decision for a dependent
question through the existing direct path. The after variant replays the frozen
dependency graph and target decisions. Both run current code and prompt metadata;
this is a controller ablation, not an old-binary run, live-model comparison or a
claim about planner quality. The model always receives the exact recorded input;
the final answer is an explicitly unscored placeholder.

[comparison-2-details.json](comparison-2-details.json) preserves all eight final
exchanges, model inputs/output records, prerequisite quotes, source text, rounds,
rankings, exclusions, stop reasons and per-case metric deltas. The earlier replay
is retained in `comparison-1-details.json`. The fixture hash is in each report.

| Variant | Recall@3 | Precision@3 | Hit Rate@3 | MRR@3 | NDCG@3 | Final span coverage |
| --- | --- | --- | --- | --- | --- | --- |
| Before: direct | .541667 | .333333 | 1 | 1 | .637926 | .458333 |
| After: dependent | .833333 | .583333 | 1 | 1 | .867320 | .750000 |

Selected candidate metrics are separate from packed-context coverage. Precision
uses denominator K even for fewer results. MRR cutoff is K; NDCG uses binary gain
and log2 discount. Final coverage requires a whole annotated canonical span in the
actual final context. Macro means cover four cases. Per-query rankings are retained
but have no separate query-specific gold judgments, so no per-query quality claim
is made. Reranking is not exercised.

Codex reviewed all four pairs against the frozen canonical texts:

- Three-hop: the direct route retains the winner and two irrelevant distractors;
  the dependent route retains winner, employer and location, with each target
  copied from the prior query's retained source. Final coverage rises from 1/3 to 1.
- Two-hop: the dependent route adds the employer, raising final coverage from 1/2
  to 1; its second search is grounded in the winner excerpt.
- Scope/no-progress: only the winner document is allowed. Both variants retain
  that one allowed gold span. The dependent route stops after its next search adds
  no canonical source text; it never reads the excluded employer/location files.
- Budget exhausted: both variants supply no evidence. The dependent route stops
  after the first round and makes no binding call. Candidate recall does not imply
  usable final evidence.

No per-case coverage regression occurs in this controlled fixture. Hand-authored
vectors and decisions intentionally expose mechanics; the aggregate gains cannot
be generalized to real retrieval, planning or answer correctness.

## Measurement boundaries

[measurement-supplement.json](measurement-supplement.json) overrides the generic
comparison inventory for both replays with complete statuses, measured retrieval
metrics and local stage/service timing distributions. It retains sample counts,
mean/P50/P95, nearest-rank method, device and resolved package versions.

The workload is sequential, concurrency 1, without live providers, model loading
or provider queue time. A cold tokenizer is possible on the first pair; the direct
control runs first, with one pass per variant. Service timing includes the local
save; affected-stage timing includes retrieval and source lookup, with individual
planning/binding/query/packing durations in traces. These are mocked diagnostics,
not production performance. No streaming first-delta latency was measured.

Answer correctness, faithfulness, completeness, relevance, citation support/coverage
and semantic abstention are not scored for placeholder answers. The live test is
skipped, and no human or LLM judge evaluated answer quality. Model usage is absent
from mock responses; evidence/local-input token counts are not provider billing.
Actual whole-turn usage/cost remains unavailable for future live acceptance.
Ingestion/index performance and throughput were not benchmarked; lifecycle behavior
is covered by isolated contract checks. Passing checks does not authorize a merge.
