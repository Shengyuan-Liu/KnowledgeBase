# Matched PDF heading-context live acceptance

Frozen before provider calls on 2026-09-29. Compare the prior six-request run at
`../20260929-new-pdf-chain/` with product commit `3fca415`. The same five-PDF
corpus, six questions, 16 facts and literal source-span labels are byte-identical.
The compared feature changes PDF parent grouping, not child content or embeddings.

## Workload and execution

Clone the stopped five-document baseline while holding its ownership lock. In
this isolated copy, rebuild parent records and child-to-parent associations using
production `join_heading_parents`, recording its version in PDF indexing metadata.
Verify all other SQLite tables, extraction, originals and vector files unchanged.
This evaluation-only operation is not a public migration feature or an upload
benchmark. Normal ingestion integration was covered by the prior scoped tests.
Public libraries still need PDF re-upload/reindexing; no existing library changes.

Run each original question once with planned retrieval, a fresh conversation,
explicit file scope, concurrency one, no warmup and zero SDK retries. Provider
and client timeouts remain 180 and 240 seconds. Use the same resolved model,
embedding, reranker, device and retrieval budgets, disclosing any runtime drift.
No paid judge, repair during the run, repeated sampling or best-answer selection.
Retain all failed attempts. Real HTTP/SSE, planning, query embeddings, retrieval,
reranking, packing, sufficiency and any supplementary retrieval execute normally.
Check saved history and original PDF bytes, ranges and revision guards. Browser
navigation is outside scope. Keep startup separate; queue/network time is included.

## Reference evidence and reviewer protocol

`frozen-cases.json` defines six unchanged questions, 16 positive expected points and
one missing-date requirement. Codex is the model reviewer, not a human reviewer.
Reuse the frozen original-page review and PNGs from `../20260929-new-pdf-chain/source-review/`; inspect the relevant retained page whenever new answer support requires it. References
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
Record parent-rebuild duration and index sizes separately from ingestion: no
upload, parsing, document embedding, user update or deletion occurs. Baseline's
one Apple upload is excluded from answer-call usage comparisons. Retain all 20
metrics and scope-specific unavailable/not-applicable reasons. Single sequential
passes cannot establish statistical quality or latency gains; these are familiar
development cases reviewed by Codex, not independent human/held-out acceptance.
