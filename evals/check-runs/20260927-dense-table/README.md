# Dense table recovery: scoped offline verification

The production parser now recovers Alabama's Permit **18,870**, Handgun
**23,022**, Long Gun **22,650**, and Totals **71,137** from the unchanged
`background-checks.pdf`. The [recorded comparison](comparison-1/run.json)
passes every frozen check for Alabama, Alaska, and Arizona. The other four
corpus documents retain byte-identical canonical text and equal structured
blocks. These are passing extraction checks on reused development material; live
retrieval, generated answers, and general dense-table accuracy were not tested.

## Frozen evidence and scope

The [protocol](protocol.md), [gold annotations](gold.json), and
[input manifest](frozen-manifest.json) retain the original question, source
hashes, annotations, and comparison scope. A separate Codex model reviewer
transcribed the original rendered page; the reviewer was not a human. Gold was
frozen after the initial exploratory native probes, before the extended
candidate and formal comparison. It was not revised to match candidate output.

The gold covers 25 positions in each of three state rows, their complete header
paths, six merged parent headers, and title/date/disclaimer controls. All refer
to physical page 1. The original file remains a one-page fixture despite its
printed `Page 1 of 205` footer. Other state rows and footer totals are ungraded;
the approximate visual gold boxes are not coordinate-overlap ground truth.

## Cause and bounded repair

All three [Docling configuration probes](docling-probes/README.md) completed
but failed to retain any of the four requested values:

| V1 accurate variant | Final table | Requested values | Conversion seconds | Command wall seconds |
| --- | --- | ---: | ---: | ---: |
| Standard backend, matching enabled | 1 × 1; 1 cell | 0/4 | 12.989 | 16.157 |
| Standard backend, matching disabled | 1 × 2; 2 cells | 0/4 | 12.808 | 15.363 |
| PyPdfium backend, matching enabled | 1 × 1; 1 cell | 0/4 | 12.675 | 15.218 |

The retained predictor inputs contain Alabama and all four original values.
Every prediction degenerates into two `ched` tokens and 1,021 `lcel` tokens,
without row separators and with only two boxes. This demonstrates loss during
TableFormer structure prediction, before the adapter. Changing matching or the
backend did not repair it. Raw native words, model inputs/outputs, documents,
logs, resolved settings, model hashes, and all three failed-quality outcomes
remain in the [probe records](docling-probes/comparison.json).

The [native experiments](native-probes/README.md) identified usable digital text
and vertical rules. Ordinary lines/text extraction omitted State / Territory
because its horizontal edges stopped inside the left border; ordinary
lines/lines extraction combined five states per band and extended into notes.
The repair extends detected text-row boundaries across the existing table crop.

[Production recovery](../../../knowledgebase/rag/pdf_tables.py) considers only
single-page Docling tables with at most one row or column, requires exactly one
native grid and a labeled numeric body, and preserves native cell rectangles,
merged spans, and explicit blanks. Values are copied from digital text; missing
numbers are not inferred. Header roles are inferred and disclosed in a warning.
Docling continues to handle layout and other tables. The parser identity records
the recovery settings and pinned `pdfplumber==0.11.9` dependency.

## Before and after

The baseline is product commit `9dcb7c5`, retained in
[baseline-pdf.py](baseline-pdf.py). The comparison replays the same five frozen
Docling documents and separately runs both production parser versions on the
original background-checks PDF. Both routes produce the same scoped scores:

| Frozen check | Before | After |
| --- | ---: | ---: |
| Numeric cells with correct row and header association | 0/66 | 66/66 |
| Explicit blanks with preserved column positions | 0/6 | 6/6 |
| State labels | 0/3 | 3/3 |
| Complete header paths | 0/25 | 25/25 |
| Merged parent header spans | 0/6 | 6/6 |
| Completely correct annotated rows | 0/3 | 3/3 |
| Original four Alabama facts with field association | 0/4 | 4/4 |

The title, November 2015 date, and disclaimer also pass all three controls after
recovery, including the distinction between background checks and firearms sold.
The [replayed review](comparison-1/review-after.json) and
[fresh production review](comparison-1/original-after-review.json) retain each
expected/observed value, header path, cell location, and match decision. Their
respective [baseline replay](comparison-1/review-before.json) and
[baseline production review](comparison-1/original-before-review.json) preserve
the failures. Exact production extractions are saved
[before](comparison-1/original-before.json) and
[after](comparison-1/original-after.json).

Apple FY24, DocLayNet, the ML lecture, and the Docling report all remain outside
the recovery gate. Each retains its source hash, canonical text, and structured
blocks in the [per-document comparison](comparison-1/run.json). The full
extraction records intentionally have new parser identities/revisions; they are
not byte-identical files. Unchanged controls preserve existing limitations,
including deferred screenshot, chart, OCR, and formula interpretation.

## Timing and measurement limits

All observations use local CPU execution on macOS ARM64, four threads,
concurrency one, no queue, and already cached model files. Each original parser
instance is used once, so its parse includes lazy model loading. OS caches are
uncontrolled. Parser construction, identity hashing, and final report writes
are outside the individual parse timer. The new parse includes native recovery;
the separate recovery observations below replay frozen documents and do not
include Docling inference.

| Measured operation | Samples | Mean / P50 / P95 seconds |
| --- | ---: | ---: |
| Original background-checks PDF, baseline production parse | 1 | 13.522032 |
| Original background-checks PDF, new production parse | 1 | 12.260421 |
| Native recovery: background-checks replay | 1 | 0.200648250 |
| Recovery gate: Apple FY24 replay | 1 | 0.000001583 |
| Recovery gate: DocLayNet replay | 1 | 0.000000584 |
| Recovery gate: ML lecture replay | 1 | 0.000000583 |
| Recovery gate: Docling report replay | 1 | 0.000001125 |

Each percentile equals its sole observation. The four control timings measure
an early gate return, not native parsing. Neither these values nor the three
instrumented diagnostic probes establish a speed improvement or a production
latency distribution. Probe conversion timings additionally include diagnostic
writes; command wall timings include interpreter and import overhead.

The [complete 20-metric inventory](comparison-1/run.json) records three measured
items and 17 `not_applicable` items, with explicit reasons:

| Metrics | Status and scope |
| --- | --- |
| Recall@K, Precision@K, Hit Rate@K, MRR, NDCG@K | `not_applicable`: no retrieval workload or ranking comparison. |
| Final evidence coverage | `not_applicable`: no final answer context was supplied; extraction scores above are separate. |
| Answer correctness, faithfulness, completeness, relevance | `not_applicable`: no generated answers. |
| Citation support, citation coverage, abstention | `not_applicable`: no answer or abstention assessment. |
| First-answer-delta latency, complete-response latency | `not_applicable`: no streaming or answer requests. |
| Stage latency | `measured`: the seven per-operation observations above. |
| Token usage and cost | `not_applicable`: zero provider calls; no billing figure is substituted. |
| Reliability | `measured`: five replay cases and two original parses completed; zero errors, timeouts, or retries in the final comparison. |
| Concurrency and throughput | `measured`: concurrency 1; 7 operations / 26.611346 seconds = 0.263046 operations/second for this mixed offline command, including hashing, recording, and review. This is not production capacity. |
| Ingestion and index | `not_applicable`: no upload, embedding, index write, update, or deletion workload. |

Local hardware/energy cost and production load capacity are unavailable. No paid
evaluation was run. Process success is distinct from extraction fidelity: all
three Docling diagnostic variants completed while failing the quality goal.

## Verification and retained attempts

- [Focused checks](focused-tests-1.json): 54 passed, no failures or skips;
  5.835 seconds command wall time. They cover the observed cells, blanks, merged
  headers, canonical offsets, physical boxes, chunk/header context, and four
  unchanged documents.
- [Backend checks](backend-tests-1.json): 764 passed, 1 skipped, no failures;
  31.429 seconds command wall time. These are offline tests, not a live RAG run.
- [Production comparison command](comparison-1.json): successful; exact
  implementation hashes, source hashes, settings, model revisions, outputs,
  and timings are retained with the [run](comparison-1/run.json).
- [Lock verification](dependency-lock-check-1.json): passed. The final lock
  scope adds only pdfplumber, pdfminer-six, and cryptography; existing package
  versions remain unchanged.

The [dependency synchronization](dependency-sync-1.json) installed the three
dependencies and also removed 69 pre-existing optional environment packages.
The [restoration](environment-restore-1.json) restored all 69 at their exact
previous versions from the retained [package list](prior-extra-packages.txt).
Both logs remain visible; this environment side effect is not omitted from the
record.

The initial native [report-link check failed](native-probes/report-review-1.json)
because it checked `measurement.json` before creating that output. The
[separate corrected review](native-probes/report-review-2.json) is retained.
Failed alternatives and attempts have not been overwritten.

## Remaining limits and use

This gate detects the observed collapsed-table shape; it is not a general table
quality detector. It does not repair incorrect multirow/multicolumn model grids.
The native probe flags possible punctuation concerns in unannotated rows,
including California's thousands separators; these are ungraded concerns, not
established regressions. No correctness claim is made for those rows, footer
totals, other layouts, or uninspected pages. Header roles and
text-row geometry remain parser estimates, and the original page remains the
reference.

The user library and historical answer snapshots were not changed by this run.
Using the repair on an existing document requires reparsing the original PDF
into a new extraction revision and rebuilding its chunks, lexical index, and
embeddings through a fresh upload/indexing pass. Existing stored chunks do not
acquire these recovered values automatically. Historical snapshots continue to
refer to their original evidence. Passing this scoped comparison does not
authorize a merge to `main` or establish live answer acceptance.
