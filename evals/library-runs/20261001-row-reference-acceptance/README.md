# Table-reference and comparison-citation live acceptance

The six frozen requests **pass 6/6 scoped gates**, compared with 5/6 in the
[preceding run](../20260929-pdf-heading-acceptance/README.md). Requested facts and
supplied evidence remain 16/16. Citation coverage improves from 18/19 to 19/19
emitted factual claims. In the separate financial controller review, all eight
requirements now select supporting rows without irrelevant selections (previously
3/8). This is one familiar development sample, reviewed by Codex, not a human or
held-out quality estimate. User acceptance and feature merge remain separate.

## Controlled scope

Product `46d5931` adds passage IDs to assessor table readings, row-selection
guidance (`evidence-sufficiency-v6`), and explicit inline-citation guidance for
comparisons. Baseline product is `3fca415`. The
[protocol](protocol.md), [six questions](frozen-cases.json), original-page facts,
and [source-span labels](frozen-labels.json) were frozen before calls.

The stopped baseline library was copied byte-for-byte into
`data/evals/20261001-row-reference-acceptance`: five PDFs, 98 pages, unchanged
extractions, children, parents, vectors and history. The questions address three
PDFs and 88 pages. No upload, parsing, reindexing or document embedding occurred.
[Execution comparison](answer-execution-manifest.json) confirms identical runtime
settings except the isolated data path, including Python, packages and device.
Original and baseline libraries remain unchanged.

Models remain `gpt-4.1-2025-04-14`, `text-embedding-3-small`, and
`BAAI/bge-reranker-v2-m3` revision
`953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e` on MPS; other local retrieval uses CPU.
The evidence cap remains 4096 tokens. Each question ran once in a fresh
conversation through planned HTTP/SSE retrieval, sufficiency and generation.
Concurrency was one, with no warmup, provider retries, paid judge, response
repair or repeated sampling. Provider/client timeouts were 180/240 seconds;
production controller limits are retained in the runtime and request traces.

## Quality and controller selections

| Case | Correct points, before -> after | Case gate, before -> after | Complete response seconds, before -> after |
| --- | --- | --- | --- |
| Paper split | 2/2 -> 2/2 | Pass -> Pass | 12.911 -> 17.428 |
| Paper delivery | 3/3 -> 3/3 | Pass -> Pass | 14.691 -> 20.978 |
| Lecture bag of words and counts | 3/3 -> 3/3 | Pass -> Pass | 8.924 -> 10.647 |
| Missing lecture date | Appropriate refusal -> appropriate refusal | Pass -> Pass | 13.016 -> 9.491 |
| Current/non-current securities | 3/3 -> 3/3 | Pass -> Pass | 8.596 -> 14.940 |
| Conditional cash flow | 5/5 -> 5/5 | Fail -> Pass | 13.880 -> 15.384 |

The [point/claim review](review.json) records correctness 16/16, completeness
16/16, faithfulness 19/19, relevance 6/6, citation support 19/19 cited claims and
citation coverage 19/19 required claims. The claim inventory includes two optional
associations between lecture counts and their probability labels; no formula
derivation is evaluated. The claim-free refusal has no citation denominator.
Appropriate abstention is 1/1 and incorrect abstention is 0/5 answerable cases.
All six saved answers, sources and retrieval traces match their streamed results.

The previously uncited cash-flow conclusion now reads:

> The fiscal 2024 amount exceeds fiscal 2023, so the condition is met [1].

Source 1 contains operating cash of 118,254 and 110,543 million for the two years;
the comparison is correct and now has its own supporting citation. Financing
cash remains an outflow of 121,983 million. No expected facts regress.

The independent [controller review](controller-review.json) compares requirements
by meaning because their IDs/order differ across samples. It distinguishes
model-selected references from application-attached table context and full
supplied source text:

| Financial diagnostic | Before | After |
| --- | --- | --- |
| Requirements with requested measure/units in selected evidence | 4/8 | 8/8 |
| Supported requirements without irrelevant selections | 3/8 | 8/8 |
| Requirements with irrelevant selections | 5/8 | 0/8 |
| Irrelevant selected reference instances | 5/10 | 0/8 |

Operating cash and the comparison now select `p19`, and financing cash selects
`p35`; the prior inventory/debt-issuance selections are absent. Securities select
the correct current/non-current rows (`p8`/`p15`) without extra inventory.
Original Apple pages 2 and 3 confirm groups, dates, units and values. Units and
group/period disambiguation remain available in full supplied context; they are
not all explicitly selected by the model. The parser still merges beginning-cash
text into the cash-flow date header. This run does not claim to fix that parser
limitation or guarantee future semantic selection reliability.

Final selected-child ranking metrics at K=5 are unchanged: macro Recall 0.650,
Precision 0.200, Hit Rate 1.000, MRR 1.000 and NDCG 0.7233 over five answerable
cases. Labels require full literal anchors and are not exhaustive semantic
relevance; the no-gold refusal is excluded. Candidate, reranked and final evidence
measurements are separate in [diagnostics](diagnostics.json). Final fact coverage
is 16/16 in both arms. Context tokens are unchanged except cash flow, 3346 -> 2986,
under independently generated plans. Assessment rounds remain 1/1/1/3/1/1.

## Performance and operational limits

| Six-request distribution, seconds | Before mean / P50 / P95 | After mean / P50 / P95 |
| --- | --- | --- |
| First nonempty answer delta | 11.330 / 12.465 / 13.979 | 13.621 / 13.939 / 18.738 |
| Complete HTTP/SSE response | 12.003 / 12.964 / 14.488 | 14.811 / 15.162 / 20.091 |

Percentiles use linear interpolation; the local refusal is included. Five cases
are slower and the missing-date case is faster in this pass. Stochastic planning,
provider cache/network/queue behavior and local compute prevent a causal latency
claim from one sample. Startup/model loading is separate at 7.847 seconds and
client readiness at 10.237 seconds. [All 20 policy metrics](measurement.json)
include affected-stage distributions; overlapping timers are not additive and
isolated search/fusion/queue times remain unavailable.

All 6/6 requests and 39/39 SDK calls complete with zero observed errors, timeouts
or retries: 6 plans, 20 query embeddings, 8 assessments and 5 generations.
Response usage is 64,483 input + 3,493 output = 67,976 tokens (before 67,335).
Reported response cached-input tokens are zero (before 1,792); query embeddings
use 480 tokens (before 522). Embedding cache usage and actual billed currency are
unavailable, not zero cost. Sequential throughput is 6 / 89.009 = 0.0674
requests/second and does not establish load capacity.

Storage grows from 58,396,481 to 63,532,865 bytes with new conversations; it includes
originals, vectors, metadata and history, not only the vector index. Indexed
database tables and historical rows are unchanged. All three queried originals
pass byte-hash, byte-range and revision-guard checks. Upload/update/delete and
browser navigation are outside this run.

## Verification and follow-up

The two scoring/mapping harness tests pass. Recorded checks cover frozen inputs,
runtime parity, original bytes, history, source offsets/pages, SDK usage, all metric
denominators and document links. The preceding implementation's 161-test result
is [recorded separately](../../check-runs/20261001-assessment-row-references/README.md);
product code did not change during this acceptance. Raw observations, answers,
reviews and every command outcome are retained here.

The server repeats the known multiprocessing semaphore-cleanup warning on
shutdown (`server.log`). Its port closes, ownership lock is released, and baseline
and indexed-state integrity checks pass; no API failure is observed from it.
Actual billing, independent human review and held-out/general quality remain
unavailable. OCR, visual charts and formula understanding are outside v2.

The next useful acceptance work is a small held-out set of new PDF questions,
especially a true dependent hop whose target is discovered from earlier evidence,
plus browser page navigation/history checks. Freeze those references before
running them. No additional live workload or merge is implied by this report.
