# KnowledgeBase v2 Release Summary

Status: functional implementation, scoped acceptance and release documentation
completed on the active `v2` branch on 2026-10-01. The user accepted this scoped
release and explicitly authorized its merge into `main` on the same date.
This is a local, single-user release; `v2` remains the active development branch.

## Delivered behavior

- Upload digitally generated English PDFs alongside TXT and Markdown. Keep original
  bytes, immutable extraction, exact source spans, supported tables and physical
  page citations. Inspect the original page from an answer citation.
- Enable **Plan complex questions** for independent question decomposition and
  evidence-dependent searches. Later targets must come from exact retained quotes;
  all searches stay within the selected ready-file scope.
- Assess supplied evidence by requested point, make bounded supplementary searches,
  and answer supported parts while identifying missing or conflicting evidence.
  Plans, source quotes and assessments persist with completed answers.
- Stop an in-progress turn, refresh saved answers, and retain historical excerpts
  after their source is deleted. Deleted originals become unavailable.

The controller permits at most six queries and three retrieval rounds, with a
finite request deadline and reserved answer time. Invalid optional supplementary
proposals are recorded and skipped; invalid mandatory judgments still fail.
No automatic response repair or unbounded retry loop is introduced.

## Use v2

Keep the existing ignored `.env` and `DATA_DIR` to retain the current library.
Install the PDF extra and local model files using the
[PDF setup instructions](../pdf-integration.md#use), then run `make app` and open
<http://127.0.0.1:8000>. Upload a PDF, wait for Ready, enable **Plan complex questions**,
ask an English question, and inspect its numbered sources and **Open page N** links.

The original `single` retrieval mode remains the default; planned mode is opt-in.
The closeout's accepted complete controller behavior is the planned mode. The
single-pass control still produced unsupported or contradictory answers on some
complex development questions. Model answers always need source inspection.

These closeout fixes operate on saved canonical extraction and require no reindex.
Older parser-version changes still require re-uploading originals to apply new
extraction; saved historical answers remain unchanged. Changing embedding models
requires a fresh index, as described in [configuration](../configuration.md).

## Acceptance evidence

The [complete closeout report](../../evals/library-runs/20261001-v2-release/README.md)
links every run, failed attempt, exact output and all 20 measurement fields.

| Population or check | Outcome |
| --- | --- |
| Matched real-PDF functional set | 6/6 cases; 13/13 expected facts supported and cited |
| Actual unknown-target execution | 1/1 synthetic chain; two rounds and exact bridge quote |
| Separate project holdout | 5/5 cases; 10/10 expected points; correct partial answer and refusal |
| A/B/C/D development comparison | 2/4, 3/4, 3/4, 4/4 case gates respectively |
| Backend | 851 passed, 1 explicitly opt-in provider smoke skipped |
| Frontend | 49 tests passed; production build passed |
| Controlled browser regression | 21 passed, including Stop and TXT/MD/PDF lifecycle |
| Real browser and lifecycle | 8 desktop/mobile checks and 9 lifecycle checks passed |

D's four-case mean first-answer delta / completion is 12.963 / 14.482 seconds,
versus 2.445 / 5.303 seconds for A. More checking adds latency and calls; these
small, sequential samples are not stable performance estimates or load tests.
The held-out five-case mean is 13.089 / 14.503 seconds, within the thresholds
frozen before opening its results. Actual billed currency remains unavailable.

The same original six questions improved from 4/6 before scope/assessment repair,
to 5/6 after those repairs, to 6/6 after continued-table evidence was fixed. The
middle run's correct financial numbers did not pass its unsupported citation gate.
The original dependency failure and control-arm regressions remain visible.

The final acceptance run used `c702c3f` product code, GPT-4.1 resolved as
`gpt-4.1-2025-04-14`, `text-embedding-3-small`, and BGE reranker revision
`953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e` on MPS. Evidence, assessment and answer
input caps were 4096, 8192 and 16384 tokens. Runtime settings and package versions
are retained in the run. Test-only version-expectation correction does not alter
that runtime. No held-out-specific model or prompt tuning followed its results.

## Known limits and deferred work

- OCR, visual chart/figure understanding and mathematical formula understanding
  are outside v2. Native text can be retained without understanding those objects.
- PDF reading order and table structure remain estimates. Complex merged tables
  and unannotated rows can fail. The closeout's continuation fix covers adjacent
  pages in the same section when currency values were misclassified as headers;
  it is not general table reconstruction.
- Planning, assessment and generation can make semantic mistakes or copy source
  bibliography markers as invalid application citations. The A/B/C control failures
  are reported, not silently corrected. Planned mode's passing sample does not
  establish error-free arbitrary-document behavior.
- The final A-D sample does not demonstrate a supplementary-search quality gain:
  the answerable evidence was already present, and the restricted gap was outside
  scope. Its execution, scope and budget controls pass controlled regression tests.
- The browser has no conversation picker, PDF zoom or selectable text layer.
  Refresh restores the current conversation; small-screen full-page text is small.
- Quality review was performed by Codex, not an independent human. The holdout is
  new to project tuning, not guaranteed absent from model pretraining. There is
  no broad statistically validated quality or production concurrency claim.
- Starlette and Docling/Pydantic deprecation warnings remain; they do not fail the
  verified flows. Provider billing and some isolated stage timings are unavailable.

These limits are the release boundary. Further refinements and newly reported
issues belong to subsequent work; they do not start an open-ended new feature
cycle inside this closeout. Merge authorization comes from the user's explicit
approval, not the completed checks. Deployment and public-quality certification
are outside this release approval; later changes require separate merge approval.

## Traceability and data

Production closeout fixes: `c702c3f`; preceding scope/optional-query fix: `d8108df`.
The final evidence and documentation commit follows these commits on `v2`.
The [development history](development-history.md) preserves the earlier sequence.

All original test PDFs, frozen protocols and run artifacts are under `evals/`.
The final isolated library is `data/evals/20261001-v2-release`; the intermediate
failed library is `data/evals/20261001-v2-closeout-matched`. Both are separate from
the user's configured library. Temporary lifecycle uploads were deleted, the
owned test server is stopped, and `.env` was not changed or committed.
