# Financial citation follow-up: six scoped requests pass the frozen review

All six requests completed, all 16 requested fact instances were correct and
complete, and all 16 current factual paragraph/bullet groups had supporting inline
citations under the unchanged review rules. The preceding run scored 13/14 for
citation coverage: its planned income first bullet was uncited. In this run both
income bullets carry `[1]` in both retrieval modes. These are six reused development
cases, not overall v2 acceptance or permission to merge.

The qualification **under the unchanged review rules** matters. The prior reviewer
explicitly accepted fiscal-Q4/full-fiscal-year wording as a reasonable inference
from the same-ending three- and twelve-month financial periods. Both current
conflict answers retain such wording. Source 1 directly supplies amounts, duration,
dates and units, but does not independently label those periods fiscal Q4/full
fiscal year. Source 2 mentions fourth-quarter adjustments and a fiscal-2024 annual
report. This report preserves the prior inference allowance for comparison; it
does not claim every qualifier is literally stated in the cited table. The
[qualifier audit](citation-qualifier-audit.json) records the distinction
without rewriting model responses or historical scores.

## Frozen scope and execution

- Product tested: `ae59147`, branch `v2`. Immediate baseline:
  [financial acceptance](../20260927-financial-acceptance/README.md), product `8f24ba3`.
- [Protocol](protocol.md) and [questions/facts](frozen-cases.json) were frozen before
  calls. Three questions cover sales, income and apparent period conflict, each in
  single/planned mode, one pass, concurrency one, retries zero. All are answerable.
- The prior inactive evaluation index was copied under its ownership lock into a
  new ignored directory. [Preparation](preparation.json) verifies 12 byte-identical
  copied files, five PDFs, 621 children, parents, extractions and stored vectors.
  No PDF was reparsed and no embedding was regenerated. The source index remains
  unchanged; new conversations are written only in the clone.
- Models/settings match the baseline except the isolated data directory:
  GPT-4.1 (resolved `gpt-4.1-2025-04-14`), `text-embedding-3-small`, hybrid K=5,
  BGE reranker on MPS, 4,096 evidence tokens, three rounds/six queries and the
  existing planner/answer token caps. The BGE revision is
  `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`.
- [Runtime](resolved-runtime.json) records settings, model/device/package versions,
  product and live-harness hashes. [Raw observations](server-observations.jsonl)
  retain exact SDK requests, results, usage and stage observations. Per-case files
  retain stream events, final sources and saved messages. No paid judge was used.

The initial preparation command lacked the project import path and failed before
copying data or calling a provider. [prepare-1](prepare-1.json) remains intact;
[prepare-2](prepare-2.json), with `PYTHONPATH=.`, completed the offline clone checks.
This is a preparation failure, not a failed answer request. The six answers were
run once; none was retried to improve the result. The evaluation server was stopped
afterward, with [start](server-start.json) and [shutdown](server-stop.json) records.

## Quality and individual outcomes

[reviewed-cases.json](reviewed-cases.json) preserves exact factual groups, citations,
point scores, evidence and grouping decisions. A Codex subagent reviewed every
answer and source; root Codex independently inspected the outputs, supporting
excerpts and original page 1. These are model reviews, not independent human labels.

| Scoped gate | Immediate baseline | Current |
| --- | ---: | ---: |
| Requests complete | 6/6 | 6/6 |
| Requested points correct and complete | 16/16 | 16/16 |
| Factual groups with supporting inline citations | 13/14 | 16/16 |
| Cited groups supported under the frozen rubric | 13/13 | 16/16 |
| Incorrect abstentions | 0/6 | 0/6 |
| Saved answer/source/retrieval parity | 6/6 | 6/6 |

The claim denominator changes with answer structure: the current income single
answer has two separate bullets, and comparison introductions/conclusions are
grouped under the retained paragraph/bullet rules. It is not a fixed 14-item test.
The missing planned-income citation is a directly inspected per-case improvement.

| Case | Current result |
| --- | --- |
| Sales / single | Both amounts, dates/periods and units are correct; all three bullets cited. Billion conversions are correctly rounded. |
| Sales / planned | Both amounts and units are correct; all three bullets cited. |
| Income / single | Both amounts/periods and units are correct; each of two bullets cited. |
| Income / planned | Both amounts/periods and units are correct; the previously uncited first item now cites Source 1. |
| Apparent conflict / single | Distinguishes the two periods with citations; fiscal-period labels use the frozen inference allowance. |
| Apparent conflict / planned | Distinguishes the two periods with citations; fiscal-period labels use the same allowance. |

For planned sales, the assessor selected the value row and date row but omitted
the period header and units. The application attached the exact period/units
passages separately under `table_context`. Income already selected its qualifiers;
the conflict case retains related headers/units as attached context. These links
make table references inspectable; they do not turn attached text into model-selected
support or prove more accurate semantic sufficiency decisions. Raw selected IDs,
assessment statuses and attached-context roles remain visible in the
[assessment-reference audit](assessment-reference-review.json).

## Evidence, usage and performance

[measurement.json](measurement.json) contains all 20 metric definitions/statuses
for baseline/current, each mode and combined, plus a separate preparation inventory.
[retrieval diagnostics](retrieval-diagnostics.json) separate vector, BM25, fusion,
reranking, final selection and evidence packing with exact rankings/exclusions.
Literal anchor coverage and reviewed semantic supplied-evidence coverage are
reported separately. Both cover all required financial points in this workload.

| Final selected children, K=5 | Baseline | Current |
| --- | ---: | ---: |
| Recall@5 | 0.777778 | 0.777778 |
| Precision@5 | 0.333333 | 0.333333 |
| Hit Rate@5 | 1 | 1 |
| MRR@5 | 1 | 1 |
| NDCG@5 | 0.777174 | 0.792836 |

These use the frozen non-exhaustive original-page anchors: recall evaluates fact
anchor coverage; precision/ranking use binary child relevance. They are diagnostics
at final candidate selection, not semantic accuracy or a new relevance gold set.

Final selected candidate ordering matches the baseline in 4/6 cases. Planned sales
uses three queries instead of two, while planned conflict uses two instead of three.
Stochastic plans and rankings limit causal attribution despite the identical stored
index and settings. One pass on these development questions does not establish
general accuracy or a production speed improvement.

Actual GPT usage is 41,878 input and 1,401 output tokens across 12 calls. Query
embeddings use 265 input tokens across nine calls. Cloning uses zero provider calls.
Actual billed cost remains unavailable; token counts are not an invented bill.
The raw artifacts and measurement record distinguish local reranking from provider
calls and preserve cached-token information where supplied.

First nonempty answer delta and complete HTTP response are measured separately.
All requests completed; the following distributions include all six per version,
with linear-interpolation percentiles and no omitted failed answer attempts.

| Timing, seconds | Baseline mean / P50 / P95 | Current mean / P50 / P95 |
| --- | --- | --- |
| First answer delta | 4.731 / 3.549 / 9.028 | 4.590 / 4.059 / 8.396 |
| Complete response | 5.673 / 5.008 / 9.781 | 5.094 / 4.509 / 8.924 |

Stage distributions retain sample counts, means, P50/P95 and workload boundaries.
No warmup answer was made; server startup/model loading is recorded separately.
Provider/network wait remains included in observed request timings and is not
independently isolated. Sequential throughput is not concurrency capacity.

## Verification and remaining limits

The command records retain successful and failed preparation, the single live pass,
retrieval analysis, measurement and offline final review. Final review checks frozen
settings/code, source and attached-reference spans, streamed/saved parity, original
index preservation, metric inventories, documentation links and stopped server.
No production implementation changed in this evaluation-only commit, so the already
passing backend suite was not rerun as a substitute for live acceptance.

This scoped citation gate passes under the stated rubric. Dense-table omissions,
unanswerable/genuine-conflict behavior, broader multi-hop quality, held-out data,
independent human review and concurrency above one remain outside this run. OCR,
visual chart/figure understanding and formula understanding remain deferred from
v2. The user still decides feature acceptance and any merge into `main`.
