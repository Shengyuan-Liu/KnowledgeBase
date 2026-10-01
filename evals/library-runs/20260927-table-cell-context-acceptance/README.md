# Explicit table readings: six-request acceptance remains open

The new representation fixes the observed grouped-column mistakes in the completed
answers, but this run **does not pass** its frozen functional gates. Five of six
requests completed. One completed answer still treats printed blanks as unavailable
information; a separate planned request failed before retrieval. No requests were
rerun. Product code was fixed at `576e772` on `v2` throughout the six requests.

## Matched results

The [previous run](../20260927-table-context-scope-acceptance/README.md) and this run
use identical questions, PDF bytes, extraction, child/parent chunks, embeddings,
source annotations and runtime settings. Only the model-facing table representation
changed. Source excerpts, coordinates, page mappings and history contracts remain.

| Question / mode | Previous correct points | Current correct points | Current observation |
| --- | ---: | ---: | --- |
| Alabama values and disclaimer / single | 5/5 | 5/5 | All values and both disclaimer clauses correct |
| Alabama values and disclaimer / planned | 5/5 | 5/5 | All points correct |
| Three state totals / single | 3/3 | 3/3 | All totals correct |
| Three state totals / planned | 3/3 | Unavailable | Planner output rejected before retrieval; three points undelivered |
| Grouped and blank cells / single | 2/4 | 2/4 | Correct Handgun and Pre-Pawn; still incorrectly treats both blanks as unestablished |
| Grouped and blank cells / planned | 1/4 | 4/4 | Correct 23,022, 14, and both empty Rentals cells |

Completed answers score **19/21 points**. Across all intended opportunities,
**19/24 points were correctly delivered**, unchanged from the previous run's 19/24.
The three points in the failed request have unavailable semantic scores, not
invented zero-valued judgments; they remain undelivered in the end-to-end gate.
Four of five completed answers satisfy every requested point. Do not call the
subset accepted based on the completed-only improvement.

The single-mode blank response says the cells are "not established in the supplied
excerpts (their values are null)". The context explicitly defines null as an empty
extracted cell, and supplies the full Alabama row and Rentals headers. This is an
incorrect omission, not a real evidence gap. The planned response correctly calls
both cells empty. Neither completed grouped answer invents a numeric rental count.
The 19 substantive factual groups have supporting citations. Following the original
baseline's grouping, the one unsupported missing-information statement is recorded
separately against its two affected points; it must accompany the factual
faithfulness/citation rates, rather than disappear behind their 19/19 denominator.

## Planner failure and preserved evidence

The provider returned valid structured JSON with four requirements and three
queries. Requirement `r4` asked to compare the three totals, but no query referenced
it. Existing `RetrievalPlan` validation rejected the plan with "address every
requirement". The [offline replay](metrics/planner-failure-replay.json) reproduces
that exact rejection using the recorded output, without a provider call or product
change. This failure happens before the changed table rendering code; the run
shows an existing planning reliability gap, not evidence of a table-rendering cause.
All raw SDK output and the HTTP 200/SSE error remain in the run.

The [actual-context audit](metrics/actual-context-audit.json) checks all five
SDK generation contexts byte-for-byte against packed evidence, including every
complete cell binding, canonical text and pages. They each use 2,518 of 4,096
context tokens and supply all 21 requested facts for those requests. The failed
request supplies no model context and has no first-answer delta.

[Offline controls](../../check-runs/20260927-table-cell-context/README.md) retain
275 passing tests and exact before/after packing replay: dense evidence 24/24,
financial evidence 16/16. Financial contexts increase to 3,664-3,981 tokens while
preserving units, periods and all requested facts. Financial answer generation was
not rerun, so broader answer behavior and other tables remain unverified.

## Quality, operations and measurement limits

The [complete metric inventory](metrics/measurement-2.json) records all 20 metrics
for each mode, all requests and shared preparation. Retrieval metrics cover the
five requests that reached retrieval: K=5 fact Recall, Hit Rate, MRR and binary
NDCG are 1.0; binary child Precision is 0.28. No retrieval metric is invented for
the failed planner request. These labels cover this annotated development subset.

| Completed requests | Samples | Mean first answer delta | Mean complete response |
| --- | ---: | ---: | ---: |
| Single | 3 | 1.969 s | 2.528 s |
| Planned | 2 | 8.005 s | 8.572 s |
| All completed | 5 | 4.383 s | 4.946 s |

The failed planned request ended after 1.484 seconds, with no answer delta.
Success was 5/6, application errors 1/6, timeouts/retries 0. The six-request command
took 26.382 seconds, giving 0.190 completed requests/second at concurrency one;
this is not load capacity. Percentiles, stage samples and failed-request timing
are retained separately. Startup is excluded from answer latency; provider/network
waiting is included. A single stochastic pass does not establish a causal speedup.

There were 22 SDK calls: 12 query embeddings and 10 GPT responses (five answers,
three plans and two assessments). Resolved GPT model: `gpt-4.1-2025-04-14`, 30,709
input tokens, 1,602 output tokens, zero reported cached input tokens. Embedding
model `text-embedding-3-small` used 319 input tokens. Billing and local compute
cost are **unavailable**, not zero. No ingestion, new parsing, indexing or paid
judge was performed. All nine assessment requirements were supported by actual
source/reference bundles; source availability alone did not prevent the single
answer's blank omission.

The [manual review](review/reviewed-cases.json) is by one Codex reviewer with a
separate mechanical audit. The previous run used two Codex reviewers. A second
independent semantic review and human review are unavailable here. Questions are
known development cases, with one observation per question/mode; do not infer
held-out or general v2 quality.

[Integrity verification](run-integrity.json) confirms the original index and `.env`
are unchanged, all five completed answers match saved evidence/history, the local
server is stopped, its port is closed and its ownership lock released. Full raw
SDK inputs/outputs, answers, source snapshots, rankings, exclusions, token usage
and failed attempts are retained. The initial harness check compared the frozen
label copy to a newly wrapped baseline metric file; the corrected check compares
the identical frozen files. It made no provider calls. The second diagnostic and
measurement artifacts correct inherited method prose only; numeric results and
raw records are unchanged. Earlier records remain append-only.

Next work should address explicit empty-cell wording and the observed unaddressed
comparison requirement. Keep these separate from parser fidelity and retrieval
coverage. No feature acceptance or merge into `main` is claimed.
