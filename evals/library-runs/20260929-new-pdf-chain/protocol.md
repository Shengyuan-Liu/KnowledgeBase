# New PDF questions through the complete answer chain

Frozen before paid calls on 2026-09-29. This is a six-request development
acceptance extension on three familiar PDFs, not a held-out corpus benchmark.
There is no component replacement or before/after quality claim in this run.

## Workload and execution

Use the committed implementation at `3333d0f` (product code unchanged since
`5541597`), dependent-planner-v8 and evidence-sufficiency-v5. Each frozen question
runs once with planned retrieval, a fresh conversation, and an explicit file
scope. Concurrency is one. No paid judge, live repair, repeated sampling, or
selection of the best answer. Preserve failed attempts. SDK retries are zero;
provider timeout is 180 seconds and HTTP client timeout is 240 seconds.

Clone the stopped `20260927-v2-pdf-live` index while holding its owner lock.
Its Apple file was deleted in the historical lifecycle test. Reingest the same
four-page Apple PDF into this isolated copy using the current parser. Reuse the
paper and lecture extraction/embeddings. Record those different extraction
vintages, all source hashes, resolved models and settings. Do not modify the
original library or delete old conversations. The other two indexed PDFs are
outside every question's explicit file scope. There is no ingestion comparison.

Run production HTTP/SSE, planning, real query embeddings, local retrieval and
reranking, evidence packing, sufficiency assessment, bounded supplementary
retrieval when selected, answer streaming and persisted-history reads. Check
original-PDF HTTP bytes, revision binding and byte ranges. Browser clicking is
not part of this run. No warmup requests; retain startup/model-load time
separately and identify the first query. Network/provider queue time is included
in observed request durations; it cannot be separated.

## Reference evidence and reviewer protocol

`frozen-cases.json` defines six new questions, 16 positive expected points and
one missing-date requirement. Codex is the model reviewer, not a human reviewer.
Inspect the seven full-page PNGs in `source-review/` before calls. References
come from original page text and table row/column associations, not model
answers. Read both financial column headings and the current/non-current row
groups. The conditional comparison is elementary arithmetic over two frozen
cash-flow values. Word-order and training-count questions use lecture prose;
formula interpretation is not evaluated. The missing-date label uses a full
75-page digital-text search and visual review of the logistics slide; it is not
an exhaustive visual search of all embedded images.

After answering, review every expected point and every substantive factual
claim against both the original pages and the exact supplied source text.
Correctness: correct expected points divided by all expected points (missing or
wrong points score zero). Completeness: explicitly addressed expected points,
separate from correctness. Faithfulness: claims supported by supplied evidence
divided by emitted factual claims. Relevance: binary per response. Citation
support: each cited claim has supporting text and correct physical page metadata.
Citation coverage: factual claims with a supporting citation divided by claims
requiring citations. A claim-free refusal has no citation denominator, not a
perfect citation score. Record appropriate refusal on the one unanswerable
question and incorrect refusal separately on the five answerable questions.
Optional factual statements in a refusal still require support and citations.

A case passes only if the response completes, every reference point is correct
and addressed (or the missing date is appropriately refused), all factual claims
are faithful with supporting citations, page metadata matches original evidence,
the response is relevant, and persisted answer/evidence/trace match the response.
Report planner classification separately: the cash-flow condition is factual
coverage, not an answer limitation rule; all entities are named, so no unknown
entity dependency is required. This sample cannot establish dependent-hop quality.

## Retrieval and operational measurements

Before answers, freeze literal anchor locations within annotated physical pages
of indexed extraction. Each numeric anchor is tied by the original-page reference
to its row, group, date and unit. These are diagnostic labels, not proof of table
understanding. A child is binary relevant if it fully contains all anchors of at
least one required fact. Enumerate every child in the allowed file for the ideal
ranking; record incomplete mapping instead of silently removing facts. Labels
do not exhaustively cover equivalent prose or reasoning-supporting neighbors.

Use K=5. Recall is relevant children retrieved divided by all labeled relevant
children; Precision divides relevant top-five children by five, even with fewer
results. Hit Rate is any relevant child; reciprocal rank is truncated at five,
with misses zero. NDCG uses binary gains and log2(rank+1) discounts with all
labeled relevant children defining the ideal. Report candidate vector/BM25/fusion,
per-query reranking, and final-round selected-child ranking separately. Average
final ranking scores across five answerable cases; no-gold refusal is ineligible.
Additionally report fact-anchor recall to distinguish child duplication from
source-fact coverage. Final supplied-evidence coverage requires all anchors of
each fact in actual supplied source ranges/text and is distinct from retrieval
and semantic answer review. Preserve rankings, exclusions and exact contexts.

Measure client first nonempty answer delta and HTTP/SSE completion separately;
metadata does not count as an answer delta. Report count, mean, P50 and P95
(linear interpolation), complete/error outcomes, and each affected stage.
Record actual embedding and response input/output tokens, cached tokens if
available, evidence tokens, SDK calls, errors, retries, timeouts, wall interval
and throughput. Actual billed cost is unavailable unless the provider returns
billing; do not invent a price. This sequential sample is not a load test.
Record Apple upload-to-ready time, index sizes and preserved originals; update
and deletion are not exercised. All 20 policy metrics must have an explicit
status, denominator/method and raw artifact. Scoped harness checks have their
own offline records; no paid calls merely to populate metrics.
