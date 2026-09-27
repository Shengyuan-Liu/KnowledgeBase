# Dense-table acceptance measurements

[measurement.json](measurement.json) is the canonical aggregate. It retains all
20 metric statuses for single mode, planned mode, all six requests, and the
separate fresh-upload preparation. The [final retrieval diagnostics](retrieval-diagnostics-2.json)
use [source-bound fact labels](fact-labels.json), frozen before answer review.
Candidate rankings, final supplied context, and independent semantic review
have separate denominators.

The scoped live acceptance failed: only 2/24 requested points are correct and
complete, and only 2/5 factual groups have supporting citations. Three full
refusals are incorrect on original-page-answerable questions. All six HTTP/SSE
requests completed, and all saved answer/source/retrieval contracts match after
excluding only the saved-history `file_deleted` flag. Three raw source-equality
flags remain false and are preserved in the source records.

All four requests that executed retrieval selected the child containing the
annotated table rows, then excluded it during evidence packing. The two
grouped-header/blank-cell requests stopped at filename scope resolution before
search or model calls. These observations do not validate live blank-cell
interpretation. Latency distributions distinguish three provider-generated
answers, one programmatic reply after retrieval, and two scope rejections.
Millisecond scope rejections must not be presented as normal answer speed.

## Reviewer sensitivity

The [primary review](../review/reviewed-cases.json) supplies the measured
relevance score: **4/6 = 0.666667**. The independent root review totals
**4.5/6 = 0.75**. The [reconciliation](../review/reconciliation.json) preserves
the three disagreements: primary scores the planned totals refusal as 1 and
both malformed-filename refusals as 0; root scores each of those refusals 0.5.
The frozen rubric does not fully specify relevance for these generic refusal
variants. The original records and primary metric are unchanged. Correctness,
completeness, supplied coverage, citation judgments, abstention counts, and the
failed acceptance outcome agree under both reviews.

## Retained evaluator attempts

- [Label binding](label-binding-1.json) succeeded before rankings or answers
  were read by the evaluator.
- [Initial retrieval analysis](retrieval-analysis-1.json) succeeded, but counted
  single-mode scope rejection as an empty executed query in stage means. Its
  [output](retrieval-diagnostics.json) is retained. The
  [corrected analysis](retrieval-analysis-2.json) excludes that unexecuted query
  while preserving zero final selected-fact coverage for the rejected request.
- [First aggregation](measurement-1.json) failed with a missing closing
  parenthesis before execution. Its log remains; it made no provider calls.
  [Second aggregation](measurement-2.json) succeeded after the syntax correction.

The raw observer records contain **19 SDK calls**: one upload embedding call,
11 query embedding calls, and seven GPT-4.1 calls. All have completed terminal
results: 16 synchronous completions and three completed streams, no SDK errors,
and retries configured to zero. Upload usage is separate from answer usage.
Actual provider billing and local compute cost remain unavailable.

[The recorded artifact review](artifact-review-1.json) checks concrete metric
artifact links, review identity, and SDK call completion. Descriptive references
such as `case-arm JSON files` are explicitly excluded from path checks and
remain descriptions of the six individual raw files.
