# Matched table-context replay: improved, still failed

At repair commit `1851615045f00d9814e01a15ff396c73ebe88f16` on `v2`, all six
requests complete and all 24 requested evidence points reach the actual model
inputs. Answer correctness/completeness improves from **2/24 to 19/24** point
instances. Four answers are fully correct. Both grouped-header/blank-cell answers
still fail, so this scoped acceptance is **not passed**.

## Matched outcomes

| Question / mode | Before correct points | After correct points | After supplied evidence |
| --- | ---: | ---: | ---: |
| dense-table / single | 1/5 | 5/5 | 5/5 |
| dense-table / planned | 1/5 | 5/5 | 5/5 |
| state-totals / single | 0/3 | 3/3 | 3/3 |
| state-totals / planned | 0/3 | 3/3 | 3/3 |
| grouped-and-blank-cells / single | 0/4 | 2/4 | 4/4 |
| grouped-and-blank-cells / planned | 0/4 | 1/4 | 4/4 |

Both modes now correctly report Alabama Permit 18,870, Handgun 23,022, Long Gun
22,650 and Totals 71,137, explain that background checks are not firearm sales,
and give Alabama/Alaska/Arizona totals of 71,137/7,095/27,087. The formerly rejected
filename/date question resolves to the same ready PDF and performs retrieval.

The remaining five wrong point instances are specific column-association and
blank-interpretation errors:

- Single mode correctly answers ungrouped Handgun 23,022 and Pre-Pawn Handgun 14,
  but labels **Redemption** Handgun 2,179 and Long Gun 2,307 as the **Rentals** values.
  Those two wrong values appear in one factual bullet citing source `[1]`.
- Planned mode correctly answers ungrouped Handgun 23,022, but substitutes
  Redemption Handgun **2,179** for Pre-Pawn Handgun **14**, and states **0** for both
  Rentals cells. The original Rentals cells are blank. Three separate bullets
  cite source `[1]` but are not supported by their actual cell associations.

This is no longer a missing-context explanation: the complete Alabama row,
Rentals parent and Handgun/Long Gun leaf headers, physical page 1, and zero-width
cell tuples for columns 16 and 17 at canonical offsets 434 and 435 are present
in the actual SDK input. Blank cells are not numerical zeros. Valid citation IDs
and numbers appearing elsewhere in the excerpt do not establish support.

There are 23 substantive factual bullet groups; 19 are supported and have
supporting citations. The four unsupported groups account for five wrong requested
points because one bullet contains two wrong Rentals claims. No full refusal
occurs; the baseline had three incorrect full refusals on answerable questions.
All six answers are relevant to their questions. No fully unanswerable questions
were included, so appropriate abstention on that population is not applicable.
Seventeen requested point scores improve and none decrease, but Q3 changes from
an operational refusal to unsupported assertions. That behavioral regression is
not hidden by the improved aggregate or by eliminating incorrect full refusals.

The [independent root review](root-review.json), [primary review](review/reviewed-cases.json)
and [reconciliation](review/reconciliation.json)
preserve point-level and claim-level judgments under the unchanged rubric. Reviewers
are Codex models, not humans; no paid judge was called. The
[actual-context audit](metrics/actual-context-audit.json) verifies all six SDK
source blocks against the final evidence, including decoded table tuples and
exact canonical bodies, headers, offsets and pages.
Both reviewers agree on all 24 points and 23 factual groups. The three actual
assessment outputs mark 12 requirements supported; that is defensible as evidence
availability because the required cells and headers are present. The assessor
returns reference IDs and status rather than proposed values, so these statuses
do not prove correct downstream interpretation. See the
[assessment/reference audit](review/assessment-reference-review.json).

## Controlled setup and limits

The [protocol](protocol.md) freezes the same three questions, both modes, expected
facts and review rules as the [failed baseline](../20260927-dense-table-acceptance/README.md).
The [source-bound cases](frozen-cases.json), [original rubric](frozen-original-protocol.md),
[gold](frozen-gold.json) and [fact labels](frozen-fact-labels.json) are byte-identical
copies. The baseline's stopped data directory was copied under its ownership lock;
the [copy record](index-reuse.json) preserves all original PDF, SQLite and vector
index bytes and historical records. No upload, parsing or document embedding was
performed for this run. Copy time is local preparation, not ingestion latency.

The [production snapshot](index-snapshot.json) has the same file ID, extraction,
ten children and five parents. Every request uses a fresh conversation. Runtime
settings, resolved reranker revision/device and dependency versions match the
baseline; the intended differences are product code and the isolated data path.
K remains 5, retrieval remains hybrid with BGE reranking, evidence budget remains
4,096, and provider retries remain zero. GPT-4.1 and `text-embedding-3-small` remain
the configured models. Exact settings and actual model revisions are retained in
[runtime](resolved-runtime.json) and [SDK observations](server-observations.jsonl).

The repaired packer supplies 3,651 tokens for five requests and 3,346 for
state-totals planned. It retains the target first child and, where also selected,
the notes child. Plans and rankings were allowed to change
naturally; this live run does not reuse offline frozen rankings as new retrieval.
Each single request executes one query; planned requests execute five, three and
four queries for dense-table, state-totals and grouped/blank cells respectively.

This is one sample per question/mode on three reused development rows. It supports
a matched scoped before/after comparison, not a held-out quality claim or a causal
estimate free of generation variability. The original-page viewer was not clicked
again; page provenance is checked in the saved sources and actual model inputs.

## Timing, records and next boundary

| Question / mode | First nonempty answer delta (s) | Complete HTTP stream (s) |
| --- | ---: | ---: |
| dense-table / single | 2.983840 | 3.760798 |
| dense-table / planned | 10.351081 | 10.957547 |
| state-totals / single | 1.513675 | 1.788371 |
| state-totals / planned | 6.481991 | 6.843035 |
| grouped-and-blank-cells / single | 1.707837 | 2.058305 |
| grouped-and-blank-cells / planned | 7.247859 | 7.810433 |

All six responses now involve generation, unlike the baseline's three generated
answers, two immediate scope rejections and one programmatic insufficiency refusal.
Compare these paths separately when interpreting latency. Timings include provider
and network waiting, exclude separately measured startup, and use concurrency one.
This workload is not a throughput/load-capacity benchmark.

For all six responses, first-delta mean/P50/P95 are
5.047714/4.732916/9.575275 seconds; complete-response mean/P50/P95 are
5.536415/5.301917/10.170769 seconds, using linear-interpolated percentiles.
Single-mode mean complete latency is 2.535825 seconds and planned-mode mean is
8.537005 seconds (three samples each). Total workload wall time is 33.415977
seconds, or 0.179555 completed requests/s at concurrency one. Startup is separate.

Exactly six HTTP/SSE requests were issued once, with 27 observed provider calls
inside them and zero preparation provider calls. Actual provider usage, means/P50/P95,
stage boundaries, retrieval metrics and all other required metrics appear in the
[complete 20-metric inventory](metrics/measurement.json). The 12 resolved
`gpt-4.1-2025-04-14` calls report 46,663 input and 1,795 output tokens, with zero
cached input tokens reported. Fifteen `text-embedding-3-small` query calls report
386 input tokens. Actual billing and local compute cost are unavailable.
There are no recorded request errors, provider errors, timeouts or retries.

At K=5, final selected-candidate fact Recall, binary-child Hit Rate, MRR and NDCG
are all 1, and mean child Precision is 0.266667. Exact stage rankings, per-query
metrics and changed plans remain in [retrieval diagnostics](metrics/retrieval-diagnostics.json).
The overall candidate scores improve partly because Q3 now reaches retrieval;
candidate ranking metrics do not substitute for the separately failed answer
scores. All before/after question/mode point scores, timings and selected IDs are
preserved in `measurement.json`'s `historical_matched_case` section.

[Integrity verification](run-integrity.json) confirms fresh conversations, frozen
snapshot identity, runtime equality, unchanged original baseline library and `.env`,
SSE answer/history parity, and final server shutdown with port and ownership lock
released. Raw history source-equality flags retain the existing schema difference:
saved sources add `file_deleted: false`; all shared source fields match.
Independent [review validation](review-validation-1.json) passes 315 provenance,
source identity and reviewer-agreement checks. These artifact checks do not change
the failed semantic acceptance result.
The [final record check](verification-1.json) passes 411 frozen-input, reporting,
provider-identity, credential-pattern and documentation checks.

The first root-review serialization attempt used a misspelled internal fact ID
and failed its aggregate assertion before writing a review. Both the
[failed record](root-review-1.json) and [corrected record](root-review-2.json) remain;
the intended manual judgments and raw answers were not revised. All evaluator
attempts and provider outputs remain append-only. No paid request was repeated to
improve the score.

The next repair boundary is table meaning in model context: present each value
with its row and complete parent/leaf column path and distinguish explicit blanks
from zero, while preserving exact source locations. The current lossless coordinate
serialization preserves information but does not ensure the model associates it
correctly. Any future representation needs offline preservation checks and a new
scoped acceptance run. These results do not authorize a merge into `main`.
