# Matched PDF heading-context acceptance

The heading-context repair recovers the lecture counts in a real first-round
answer. All **16/16 reference points** are now supplied and answered correctly,
up from 14/16. The complete acceptance gate remains **5/6**: the cash-flow answer
introduces an uncited comparison bullet. The lecture improves and the cash-flow
case regresses on citation coverage. Do not interpret this as full acceptance.

## Frozen comparison and execution

Compare [the original six-question run](../20260929-new-pdf-chain/README.md) with
product commit `3fca415`, following the unchanged answer/claim rubric in the
[protocol](protocol.md). The [questions](frozen-cases.json) and
[source-span annotations](frozen-labels.json) are byte-identical. There are five
indexed PDFs / 98 pages, with three PDFs / 88 pages explicitly scoped by questions.
These are familiar development documents, not held-out generalization evidence.
Codex performed the model review; there is no independent human or paid judge.

The stopped baseline index was copied under its ownership lock into
`data/evals/20260929-pdf-heading-acceptance`. An evaluation-only
[parent rebuild](parent-rebuild.json) applies the production grouping function
to the frozen extraction. All 621 child texts/IDs/offsets/headings, vectors,
extraction revisions, originals and historical rows remain unchanged. Only parent
records, child links and the PDF grouping-version metadata change. Parent counts
are lecture 100 -> 89, Apple 8 -> 4, technical report 21 -> 20; paper 22 and
background checks 3 are unchanged. No parsing, upload or document embedding runs.

This controlled rebuild bypasses public re-upload. It is not a product migration
or a new upload benchmark. Normal ingestion was covered by the prior
[177-test regression](../../check-runs/20260929-pdf-heading-context/README.md).
Users still need to reindex/re-upload existing PDFs to get new parent associations.
The original library and baseline evaluation directory were not modified.

[Runtime comparison](answer-execution-manifest.json) confirms the same settings
except the isolated data path, including packages, Python, device, budgets and
models: `gpt-4.1` resolved to `gpt-4.1-2025-04-14`, `text-embedding-3-small`, and
`BAAI/bge-reranker-v2-m3` revision
`953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e` on MPS. Local retrieval uses CPU.
The context cap is 4096 tokens. Six sequential fresh conversations each ran once
through production HTTP/SSE, real planning/query embeddings, retrieval/reranking,
packing, sufficiency and answer generation. No warmup or retry; provider/client
timeouts are 180/240 seconds. New plans and later rankings were allowed to differ.

## Quality and remaining failures

| Case | Correct points before -> after | Case gate before -> after | Assessment round before -> after |
| --- | --- | --- | --- |
| Paper split | 2/2 -> 2/2 | Pass -> Pass | 1 -> 1 |
| Paper delivery | 3/3 -> 3/3 | Pass -> Pass | 1 -> 1 |
| Lecture bag of words and counts | 1/3 -> 3/3 | Fail -> Pass | 3 -> 1 |
| Missing lecture date | Appropriate refusal -> appropriate refusal | Pass -> Pass | 3 -> 3 |
| Current/non-current securities | 3/3 -> 3/3 | Pass -> Pass | 1 -> 1 |
| Conditional cash flow | 5/5 -> 5/5 | Pass -> Fail: missing citation | 1 -> 1 |

The lecture now supplies both page-62 learning bullets with source `[4]` and
answers document counts per topic and word counts within each topic. It needs no
supplementary round. Final evidence and answer correctness/completeness both
reach 16/16, but these remain separate measurements. There are no lost expected
facts. The missing-date case appropriately refuses (1/1); incorrect abstention on
answerable cases falls from 1/5 to 0/5.

All **19/19 emitted atomic factual claims** are supported by supplied evidence;
all 18 actually cited claims have supporting citations. Citation coverage is
**18/19**, down from 15/15 in the baseline. The new claim inventory includes the
two recovered counts and two optional count-to-probability-label associations.
The claim-free refusal has no citation denominator. Relevance is 6/6, and all
six saved answers, evidence and retrieval traces match their streamed responses.
See [point/claim review](review.json) and [failure analysis](failure-analysis.json).

The precise failing cash-flow bullet is:

> Since $118,254 million (2024) exceeds $110,543 million (2023), the comparison condition is met.

Its arithmetic is correct, but it lacks an inline citation under the unchanged
per-item rule. Source 1 and a source-number mapping were available to generation;
neighboring cited bullets do not satisfy this item's citation requirement. No
citation was inserted afterward and no paid rerun was used to obtain a pass.

Additional controller inspection finds four cash-flow requirements marked
supported using the wrong selected rows: operating amounts/comparison point to
`Inventories`, and financing outflow points to `Proceeds from issuance of term
debt, net`. Correct rows are present in the same context. The securities assessor
also includes an irrelevant inventory row alongside the correct non-current
securities row. The final generator sees the complete source and gives correct
values despite these selections. Valid passage IDs and exact quotations do not
establish semantic support. These are separate controller diagnostics, not a
post-hoc change to the frozen final-answer gate. No causal connection between
these errors, regrouping and the citation omission is established by one pass.

The factual cash-flow comparison stays a requirement, not an answer rule. Units
also become a requirement in this sample, while the baseline used an answer rule;
the answer still states them. No unknown-entity dependent hop is exercised.

Final-round selected-child ranking metrics at K=5 are unchanged: Recall 0.650,
Precision 0.200, Hit Rate 1.000, MRR 1.000, NDCG 0.7233. Labels require complete
literal anchors within frozen physical pages and are not exhaustive semantic
relevance. The five answerable cases define the macro mean; the no-gold refusal
is excluded. Candidate vector/BM25/fusion, per-query reranking and final supplied
evidence remain separate in [diagnostics](diagnostics.json). No ranking gain is
claimed from increased parent-context coverage.

## Performance and measurement boundaries

| Six-request distribution, seconds | Before mean / P50 / P95 | After mean / P50 / P95 |
| --- | --- | --- |
| First nonempty answer delta | 12.868 / 13.503 / 17.233 | 11.330 / 12.465 / 13.979 |
| Complete HTTP/SSE response | 13.618 / 14.431 / 18.213 | 12.003 / 12.964 / 14.488 |

Percentiles use linear interpolation, including the local refusal. The lecture
completes in 8.924 seconds versus 15.462; the missing-date case slows from 8.336
to 13.016 seconds. These are single samples affected by stochastic plans, provider
cache/network/queue behavior and local compute, not a proven latency improvement.
Server model/startup time is separate at 4.700 seconds; client readiness is 6.174
seconds. Stage distributions and counts are retained in the
[complete 20-metric inventory](measurement.json). Search/fusion and provider queue
times cannot be isolated. Overlapping stage times are not additive.

All six requests and 40/40 SDK calls complete, with zero observed errors,
timeouts or retries: 6 plans, 8 assessments, 5 generations and 21 query embeddings.
Comparable baseline answer calls total 43; its one document-embedding batch is
excluded from this comparison. Response usage is 63,820 input + 3,515 output =
67,335 tokens (baseline 72,056); query embeddings use 522 tokens (baseline 491).
Reported response cached-input tokens are 1,792. Embedding cache usage and billed
currency are unavailable; missing billing is not zero cost. Sequential throughput
is 6 / 72.145 = 0.0832 requests/second and does not establish load capacity.

Parent rebuild takes 0.279 seconds including integrity checks (one operation;
mean/P50/P95 equal that observation). Storage is 53,018,433 bytes before rebuild,
53,460,801 after rebuild and 58,396,481 after answers, including PDFs, vectors,
metadata and historical/new conversations. This is not vector-only size or
upload-to-ready latency. All three queried original-PDF byte hashes, byte ranges
and revision guards pass. No public update or deletion is exercised.

## Verification and follow-up

The two offline scoring/mapping tests pass. Frozen-input/runtime, rebuild,
original-access, answer-history, token-usage, review and artifact checks are
retained with their command records. Product code is unchanged in this run; the
177-test result belongs to the preceding implementation, not a new test claim.
All run commands succeed. The server emits one multiprocessing semaphore-cleanup
warning on shutdown, retained in `server.log`; its port closes, the ownership lock
is released, indexed tables and historical rows are preserved, and the baseline
directory remains unchanged. No API failure is observed from that warning.

The heading/count retrieval miss is resolved in this bounded sample. Next,
investigate the frozen financial assessor row selections and citation coverage
for comparison conclusions. Use scoped offline regressions before another
bounded acceptance run. Broader held-out, dependent-hop and browser acceptance
remain separate. This run does not authorize a feature merge.
