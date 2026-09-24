# Test and Experiment Measurement Policy

Every future test or experiment must have a retained record. This policy is a
reporting requirement; it does not claim that existing runners automatically
calculate all metrics. Add missing measurements within the authorized work and
mark remaining gaps explicitly. Historical artifacts remain unchanged.

## Run record

Store each run under a new directory in `evals/runs/`, `evals/library-runs/`,
`evals/browser-runs/`, or `evals/check-runs/`, according to its scope. Keep raw
outputs and a concise report together. A coherent verification session can group
multiple commands, but must retain the result of each invocation, including
failed attempts. Never overwrite earlier results when retrying.

Record the purpose, timestamp, code commit and uncommitted-change identification,
commands, dataset/corpus/annotation versions, resolved settings, model/revision,
device, concurrency, warmup/cache conditions, timeout/retry configuration and
review protocol. Preserve exact candidates, ranks, supplied evidence, answers,
errors and per-question scores for RAG experiments. Do not store credentials.

For every metric below, supply:

- Status: `measured`, `not_applicable`, or `unavailable`.
- Value and unit for measured results; otherwise null and a concrete reason.
- Sample count or numerator/denominator, population, method and aggregation.
- Artifact location for raw observations or review evidence.

`not_applicable` means the run does not exercise that behavior. `unavailable`
means the behavior is relevant but its measurement, annotation or instrumentation
is missing. Missing measurements cannot support an improvement claim. Do not
silently drop failed requests from reliability or end-to-end acceptance rates.

## Required metric inventory

| Metric | Required definition or qualification |
| --- | --- |
| Recall@K | Relevant units retrieved in the first K divided by all labeled relevant units; record K and label completeness |
| Precision@K | Relevant units in the first K divided by K; disclose handling of fewer than K results |
| Hit Rate@K | Fraction of eligible queries with at least one relevant result in the first K |
| MRR | Mean reciprocal rank of the first relevant result; disclose search cutoff and score misses as zero |
| NDCG@K | Ranking quality against ideal relevance order; record relevance grades, gain and discount conventions |
| Final evidence coverage | Coverage of annotated source characters, spans or facts in the actual model context; distinguish partial and fully covered evidence |
| Answer correctness | Agreement with reference facts; identify reference scope/version and scoring rubric |
| Faithfulness | Support for the answer's factual claims in the supplied context, assessed separately from reference correctness |
| Answer completeness | Coverage of required answer points; facts present only in context do not count as answered |
| Answer relevance | Whether the response addresses the question without irrelevant material; record rubric |
| Citation support | Whether cited passages support the associated claims; valid citation IDs alone do not count |
| Citation coverage | Fraction of factual claims requiring citations that have supporting citations; define treatment of claim-free answers |
| Abstention | Appropriate abstention rate on unanswerable questions and incorrect abstention rate on answerable questions, with separate denominators |
| First-answer-delta latency | Request start to first nonempty answer delta; not a metadata event or buffered response completion |
| Complete-response latency | Request start to complete answer/HTTP completion; specify the endpoint and stop event |
| Stage latency | Query embedding, search/fusion, reranking, evidence packing and generation; record stage boundaries and queue inclusion |
| Token usage and cost | Actual provider input/output usage and available billed cost; separately record evidence tokens and local compute; unavailable cost is not zero |
| Reliability | Success, error, timeout and retry counts/rates; identify requests versus attempts |
| Concurrency and throughput | Concurrency, completed requests per measured wall-clock interval, and latency under that workload; sequential runs do not establish load capacity |
| Ingestion and index | Upload-to-searchable duration, index size and update/delete verification for ingestion/lifecycle runs; record corpus size and reindex requirements |

Evaluate retrieval/reranking and final packed evidence separately. Fix the
evaluation unit (document, child, source span or fact); never compare scores
computed over different units as if they were equivalent. When chunking changes,
prefer stable source-span/fact annotations. Incomplete relevance labels must be
disclosed, especially for precision and ranking claims. Unanswerable questions
with no gold evidence are not zero-recall cases.

Report sample counts, means, P50 and P95 for measured latency distributions,
including the percentile method and treatment of failures. Keep cold start/model
loading separate, and state whether queue waits are included. Report per-case
quality changes alongside aggregates and split important question categories.
Use the same workload and reviewer protocol for comparisons; disclose any other
changed settings and avoid inferring causality from a noisy single pass.

Keep correctness, completeness, faithfulness and citation scores distinct. If
using an LLM judge, record its model, prompt/rubric version, failed judgments and
human inspection coverage. Do not label Codex or another model as a human reviewer.

## Scope-specific records

- **Offline tests:** retain command output, code version, duration,
  pass/fail/skip counts and failure details. List the metric inventory above with
  scope-appropriate statuses. Mocked-provider timings are test durations, not
  production latency. Live answer quality and provider cost are not applicable.
- **Live RAG experiments:** measure the applicable retrieval, generation and
  operational dimensions above. Missing labels or unimplemented instrumentation
  are `unavailable`, with reasons and any implications for acceptance. Preserve
  unresolved failures in the delivery summary.
- **Load or ingestion tests:** measure the exercised workload and lifecycle
  dimensions; do not claim untested answer quality or concurrency capacity.
- **Documentation-only changes:** retain content/link/format review results in
  the commit description or a check record. Automated tests and runtime metric
  measurements are not applicable. No live benchmark is required.

This policy does not authorize additional paid workloads or changes outside the
user's task. It also does not authorize merging: the user decides acceptance and
explicitly approves each feature's merge into `main`.
