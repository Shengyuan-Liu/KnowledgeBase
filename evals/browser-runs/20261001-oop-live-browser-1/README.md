# Real-browser verification after the OOP refactor

Code: `d6e99d6` on `v2`, 2026-10-01. Google Chrome 154.0.8037.58 ran with a visible
window against the production application and freshly built frontend. The user
authorized reuse of the configured OpenAI key. No mock providers or application
code changes were used. Storage was isolated under
`data/live-browser/20261001-oop-live-browser-1`; the user's library was not opened.

**Result: the main workflow works, with a confirmed source-scope defect.**
The test service and browser were shut down after verification.

## Verified behavior

- Four uploads reached Ready: TXT, Markdown and two one-page digital PDFs.
- Weekday hours and a conversational Saturday follow-up returned the correct
  5 PM / 7 PM facts with source citations.
- Markdown retrieval returned the 24-hour reservation rule and second-floor
  location. Citation inspection displayed the actual source passage.
- A planned PDF question executed two rounds: retrieve the Juniper assignment,
  bind `Quenwick Laboratory` to an exact assignment quote, then retrieve its
  17-day calibration interval. The trace records an executed dependency and a
  supported final evidence assessment. Both answer claims cite the correct PDFs.
- The original PDF rendered at page 1 in the in-app viewer. Desktop and 390-pixel
  mobile evidence views were readable on visual inspection.
- Refresh restored messages, evidence, planning and diagnostics.
- Stop interrupted generation; the partial turn was not persisted and disappeared
  after refresh.
- Deleting the test assignment PDF removed its original endpoint (404) while
  retaining historical answer excerpts with the deleted-source indicator.
- An explicitly scoped question about an unknown PIN correctly explained that
  the source did not contain it.

## Confirmed failure

With `cedar-hours.txt` still Ready and explicitly stating the weekday closing time:

> Using only my uploaded documents, when does Cedar Library close on weekdays?

Expected: 5 PM, with a supported citation.

Observed: `I could not find a ready document matching "my uploaded documents".`
No evidence was retrieved. The source-reference parser treats the generic phrase
as a filename because `my` is absent from its generic-source word set. The parser
is byte-identical at `bbd0a8d` and `d6e99d6`; see
[scope provenance](scope-provenance.json). The defect remains unfixed because this
request was verification, not a new source-scope implementation change.

The initial unanswerable-PIN question exposed the same problem. Its broad regex
smoke assertion passed, but semantic review rejects its incorrect missing-file
explanation. The raw workflow result is retained unchanged; the
[review](review.json) and [measurements](measurement.json) explicitly record the
failure. A subsequent explicit-filename PIN question verifies actual source-based
abstention. The answerable generic-source case still fails.

## Observed timing

Browser fetch start to a nonempty answer delta / complete SSE event, concurrency 1:

| Response type | N | First delta mean / P50 / P95 | Complete mean / P50 / P95 |
| --- | ---: | --- | --- |
| Ordinary model answers | 3 | 3.02 / 3.26 / 4.30 s | 4.24 / 3.49 / 7.23 s |
| Planned two-round PDF answer | 1 | 11.72 / 11.72 / 11.72 s | 13.06 / 13.06 / 13.06 s |

Percentiles use nearest rank. Model loading and uploads precede these answer
timings; network and provider queue time are included. The fast scope-error
response and intentional cancellation are retained separately. Supplemental probes
record UI-ready duration but lack first-delta and complete-SSE arrival timing.
These small samples do not establish production latency or load capacity.

Upload-to-Ready observations were 2.36 s (TXT), 0.81 s (Markdown), 2.80 s (first PDF,
including lazy converter initialization) and 0.79 s (second PDF). See
[stage summaries](stage-summary.json) for affected-stage sample counts and
mean/P50/P95 values; overlapping stage totals must not be summed.

## Quality and limits

Codex reviewed all seven unique completed cases and the exact supplied evidence;
this is model review, not independent human ground truth. Five cases passed the
semantic review; both generic-source cases failed. Across five answerable cases,
six of seven expected facts appeared in supplied evidence and in the answer;
the remaining fact was lost to the confirmed false refusal. All seven substantive
claims in the five useful answers had supporting citations. Refusal and missing
answers are reported separately, so high citation support does not hide the failure.

The complete metric inventory is in [measurement.json](measurement.json):
document-level Recall/Precision/Hit Rate@5, MRR, NDCG, separate retrieval/rerank/final
evidence stages, source-fact coverage, answer review, abstention, browser/stage
latency, usage, reliability and ingestion/index observations. Precision keeps a
denominator of five when fewer documents are returned. This tiny, explicitly scoped
synthetic corpus is not a general retrieval-quality benchmark.

The configured answer model was `gpt-4.1`; structured planning/binding/assessment
responses resolved to `gpt-4.1-2025-04-14`. Local reranking used
`BAAI/bge-reranker-v2-m3`, revision
`953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`, on MPS. The embedding model was
`text-embedding-3-small`. Exact answer/embedding response revisions and token usage
were not exposed by the production HTTP/history interface. Four structured-call
usage records are retained. Billing was unavailable; no cost is invented.

Nine stream requests started: eight persisted completed exchanges and one intended
cancellation. One completed exchange belongs to the failed supplemental harness
attempt and duplicates the generic-source question; it remains in the final
snapshot but does not count twice in unique-case scores. There were no JavaScript
page exceptions or server 5xx errors. A favicon request returned 404. Browser aborts
occurred during cancellation, PDF viewer cleanup and post-delete refresh; the
expected server state was verified. No throughput, complex-PDF fidelity or live
pre-refactor comparison was measured.

## Retained attempts and evidence

- `build.json` / `build.log`: frontend typecheck and production build passed.
- `browser.json` / `browser.log`: main Chrome workflow passed its UI assertions;
  semantic review subsequently identifies the generic-source failure.
- `scope-probe-command.json` / `.log`: first supplemental attempt failed in
  Playwright response-body capture after the UI consumed the SSE response.
- `scope-probe-command-2.json` / `.log`: one semantic check passed and one failed.
  Unavailable response bodies are recorded in `scope-probe-2-stream-errors.jsonl`;
  complete answers remain available in history snapshots.
- `protocol.json`, `scope-probe-2-protocol.json`: frozen questions and expected facts.
- `streams.jsonl`, `answer-*.json`, `storage-*.json`: exact events, rankings,
  exclusions, evidence, answers, PDF extraction records and persisted histories.
- `environment.json`, `server.log`: redacted settings, source hashes, versions,
  device, startup/shutdown and HTTP observations.
- `review.json`, `measurement.json`, `stage-summary.json`: final reviewed outcome,
  complete metric inventory, explicit missing values and timing summaries.

Screenshots: [PDF viewer](pdf-viewer.png), [planned evidence](planned-evidence.png),
[mobile evidence](mobile-evidence.png),
[confirmed false refusal](generic-source-answerable-2.png),
[correct abstention with an explicit filename](explicit-source-unanswerable-2.png).

All attempts are retained. No merge into `main` is authorized by these checks.
