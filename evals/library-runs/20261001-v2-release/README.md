# v2 functional closeout

**The scoped v2 functional gates pass on `v2`.** Runtime code is `c702c3f`;
subsequent edits correct one stale test version and publish the evidence. User
acceptance and an explicitly authorized merge remain separate.

## Fixed scope and outcome

| Gate | Result | Evidence |
| --- | --- | --- |
| Same six original questions | 6/6 pass, 13/13 requested facts supported and cited | [Review](review.json), [diagnostics](diagnostics.json) |
| Real dependent execution | 1/1 synthetic chain, 2/2 facts, two rounds, literal bridge quote retained | [Dependency comparison](dependency-review.json) |
| Separate project holdout | 5/5 cases, 10/10 expected points, 14/14 factual groups supported/cited | [Held-out review](heldout-review.json) |
| Four-arm comparison | A 2/4, B 3/4, C 3/4, D 4/4 | [A-D review](ablation-review.json), [frozen protocol](ablation-protocol.json) |
| Actual saved answers in browser | 8 checks pass across 1440px and 390px | [Browser result](browser2-result.json) |
| Real PDF/TXT/MD lifecycle | 9 checks pass; saved evidence remains after deletion, original returns 404 | [Lifecycle completion](lifecycle-completion.json) |
| Backend | 851 passed, 1 opt-in live test skipped | [Final command](backend-final-retry.json), [output](backend-final-retry.log) |
| Frontend and build | 49 tests pass; production build passes | [Frontend](frontend-final.json), [build](build-final.json) |
| Controlled browser regressions | 21 pass, including Stop during planning/binding/assessment/generation | [Command](browser-regressions.json), [output](browser-regressions.log) |

The skipped backend test is the standalone `API_OK` provider smoke, gated by
`RUN_LIVE_API_TESTS=1`; real provider behavior was exercised by the retained RAG
requests instead. Starlette and Docling/Pydantic deprecation warnings remain.

## Matched failures and repair

The original [first-use acceptance](../20261001-new-pdf-acceptance/README.md)
passed 4/6 cases: generic document wording blocked all financial searches and an
invalid optional supplementary query aborted a valid partial assessment. The
[initial closeout replay](../20261001-v2-closeout-matched/README.md) confirmed those
repairs but passed only 5/6 citation gates. It also retained the failed synthetic
binding attempt. No failed output was overwritten.

The narrow `c702c3f` repair attaches exact prior-page table headers and units to
the observed continuation, and separates an unknown search identity from its
not-yet-retrieved attribute. Its [105 scoped checks](../../check-runs/20261001-v2-closeout-fixes/README.md)
pass. The final matched replay passes 6/6 and the same dependency question passes
with actual target binding. PDF bytes, canonical extraction, chunks, models and
retrieval budgets are unchanged. No reingestion is needed for these two repairs.

The RAG/DPR answer still uses independent searches. It is a correct answer, not
proof of dependent execution. The fictional laboratory chain supplies that
separate proof without injecting a target or plan into the request.

## A-D comparison and cost of checking

Four fixed development cases cover simple prose, restricted missing evidence,
financial periods/bases and an unknown target. All use the same six-file index,
file boundaries, base answer prompt, models, reranker and 4,096-token context.
D reuses its declared final matched outputs. B changes only the planning route
instruction and disables assessments; C enables dependency binding but disables
sufficiency actions. D additionally supplies its assessment to generation, an
explicit component difference. No answer output is repaired.

| Arm | Gate | Mean first delta | Mean complete response | Provider calls |
| --- | --- | --- | --- | --- |
| A: single pass | 2/4 | 2.445 s | 5.303 s | 8 |
| B: independent decomposition | 3/4 | 9.051 s | 10.668 s | 19 |
| C: dependent retrieval | 3/4 | 9.955 s | 11.972 s | 20 |
| D: sufficiency controller | 4/4 | 12.963 s | 14.482 s | 25 |

Each timing population has four sequential requests; P50/P95, usage and stage
breakdowns are retained in [final measurements](measurement-final.json). These
one-pass results do not isolate cache effects or establish stable speed differences.

A invents missing DPR training details and gives a contradictory financial answer,
including 82,722, a later 86,789 calculation, and a final refusal. Every part counts
in review; the convenient intermediate correction is not selected as its answer.
B and C preserve the missing-evidence boundary but copy the paper's bibliography
marker `[26]` into an answer whose application sources have different IDs. Those
case gates fail despite otherwise supported facts. D passes this limited sample
with greater latency and provider usage. Single mode remains the existing default;
use **Plan complex questions** to exercise the accepted v2 controller.

Four additional assessments of C's frozen final contexts execute no new searches
and never change C's answers. All 11 reviewed requirement statuses agree with the
reviewed evidence: ten supported and one restricted missing point. The one gap
proposal is not executed. **This sample does not establish a supplementary-search
coverage benefit:** C already holds the answerable evidence, and its restricted
missing fact cannot be found within scope. Supplementary-search mechanics and
bounds are covered by controlled tests, not a claimed live quality improvement.

## Held-out boundary

The [two original papers and five-question protocol](../../materials/pdf-v2-closeout-heldout/README.md)
were frozen before ingestion and application answers. The code/configuration was
fixed and no held-out result was used for tuning. Three fully answerable questions,
one partial question and one unanswerable question pass their frozen point,
citation, scope and abstention gates. All first deltas are below 60 seconds and
all completions below 90 seconds; means are 13.089 and 14.503 seconds respectively.
These are functional thresholds, not production SLOs.

The papers are new to this project, not necessarily new to the model's pretraining.
Codex reviewed original rendered pages and every emitted substantive claim; no
independent human review or statistical generalization claim is made. The synthetic
laboratory case is development/controller evidence and is excluded from this holdout.

## Browser and lifecycle

Actual saved answers render their original PDFs at desktop and mobile widths.
Financial source 2 opens physical page 7's units/period headers and page 8's values;
lecture page 35 remains distinct from printed Slide 69. Navigation, close/reopen,
dependency target quotes and refresh restoration pass. The harness switches
existing conversation IDs through localStorage because there is no product history
picker; ordinary refresh uses the product behavior. Mobile full-page fit is small;
this is not a zoom/readability acceptance.

The live lifecycle uploads PDF, TXT and Markdown through the UI, asks one real
planned PDF question, reloads it, deletes all three probe files, and confirms
saved text plus unavailable-original behavior. Controlled provider browser tests
supply deterministic cancellation coverage without extra paid cancellation runs.

## Complete evidence and operational limits

[measurement-final.json](measurement-final.json) contains all 20 required metrics
for each answer population, candidate/fusion/reranking diagnostics at K=5/20,
final supplied-child ranking at K=5, claim/point review, latency distributions,
usage, reliability, ingestion and lifecycle observations. Original frozen anchors
are incomplete semantic relevance labels; held-out rankings use coarser original
page labels frozen before answers. Neither is silently equated with semantic
supplied-evidence coverage. Exact SDK inputs/outputs, final excerpts, rankings,
exclusions, plans, assessments and history snapshots remain beside the report.

The final run makes **126 unique provider calls**, all terminal, with zero SDK
errors, timeouts or retries, and **260,049 total reported tokens**. These include
five document embedding calls, 56 query embedding calls, four C shadow assessments
and the real UI lifecycle. Reused D artifacts are not double-counted. The failed
initial closeout run has separate usage records and is not included in this total.
Actual billed currency and isolated provider-queue/search/fusion timings are
unavailable. No paid judge was used.

The two new papers ingest in 10.995 and 9.174 seconds. The final isolated library
has 8 PDFs, 123 physical pages, 792 children and 211 parents. Canonical extraction,
chunks and all original hashes match before/after checks; temporary lifecycle
files are removed. [Final index check](final-index-check-final.json) and
[shutdown confirmation](server-stop.json) show the owned server stopped, port 8787
free and the data lock released. Data remains at `data/evals/20261001-v2-release`;
user library and `.env` were untouched.

Failed check attempts remain: the original matched citation/binding failures;
a stale v5-versus-v6 test expectation in the first full backend run; a browser
selector choosing a hidden duplicate; a lifecycle request lacking an absolute
URL; and shutdown checks observing relative command spelling and the socket closing
before lock cleanup. Each has a successful scoped follow-up. The intermediate
measurement grouped one unlabeled browser query embedding with ingestion; the
append-only final measurement corrects that bucket without changing totals.

The remaining parser fidelity limits, unsupported OCR/figures/formulas, model
mistakes and missing independent validation are explicit release limitations.
This closeout does not authorize a merge or promise error-free arbitrary PDFs.

Final documentation review checks 17 Markdown files and 199 local links, with
no missing targets, unbalanced fences or secret findings. Product hashes and
held-out protocol match the pre-answer freeze; `.env` is unchanged and ignored.
The small final wording edits identify historical versus current review records
and implemented module paths; they add no links or runtime changes.
