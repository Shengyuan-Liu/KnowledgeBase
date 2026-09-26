# Parent Reranking Acceptance

Whole-parent scoring plus a 6144-token evidence budget recovers both observed
semantic omissions on this frozen development set. **Neither setting becomes the
default.** Structural parent-child ingestion with the existing child scoring
already covered these facts. Parent scoring adds local compute and supplies more
text; it is not a demonstrated general improvement over that simpler control.

## Controlled retrieval comparison

The experiment fixes 17 documents, 24 questions (21 answerable), source-span
annotations, stored child/parent boundaries, saved vector top-20, recomputed
BM25 top-20/RRF, local BGE revision and top K=5. Eight combinations exercise both
indexes, child/parent scoring and evidence budgets 4096/6144. All **192 replays
succeeded**. Child scores are reused only after exact question/candidate-input
checks; parent scores are computed once per question/index, then reused for the
other budget. These are 48 local inference calls, not 192 fresh model calls.
No embedding, ingestion or provider generation occurs in the retrieval phase.

| Index / scoring / budget | Mean annotated-span coverage | Fully covered gold-span fraction | Changed cases versus that index's child/4096 control |
| --- | ---: | ---: | --- |
| Structural / child / 4096 | 99.967% | 76.19% | Control |
| Structural / child / 6144 | 99.967% | 76.19% | None |
| Structural / parent / 4096 | 99.967% | 76.19% | None |
| Structural / parent / 6144 | 99.967% | 76.19% | None |
| Semantic / child / 4096 | 95.205% | 71.43% | Control |
| Semantic / child / 6144 | 95.205% | 71.43% | None |
| Semantic / parent / 4096 | 97.586% | 73.81% | Working/enrollment: 50% → 100% |
| Semantic / parent / 6144 | 99.967% | 76.19% | Working/enrollment and CPT: each 50% → 100% |

There are no other source-span coverage changes, including regressions. Five
DeepSeek annotations retain the previously documented newline-only coverage gaps;
fully covered spans therefore remain below 100% despite negligible character loss.
Parent scoring admits the admissions CPT parent at rank 4, but the earlier
parents leave insufficient room at 4096 tokens. A larger budget alone does not
fix child selection. Both effects are necessary for this particular omission.

`comparison.json` retains per-case deltas. Every variant JSONL retains exact
scored inputs, raw route/rerank ranks, selected representative children, packed
sources and budget exclusions. Stage coverage distinguishes representative child
intervals from whole scored parent regions. Recall, Precision, Hit Rate, MRR and
NDCG use K=5 immutable parser-block projections with incomplete binary gold-overlap
labels; these source-order proxies are secondary diagnostics, not equivalent
native child rankings or exhaustive relevance judgments.

The old child/4096 source text, offsets, IDs and matched-child associations were
reproduced exactly for both indexes. Default behavior remains unchanged.

## Performance and bounded live probe

On MPS, batch 4, the same BGE revision scored whole parents using pair limit 2048
and total input cap 32768. Mean parent-rerank time was 6.646 s on structural
children (P50 6.616, P95 9.029; n=24) and 4.899 s on semantic children (P50 4.236,
P95 8.690; n=24), excluding separately recorded loading. Cached child/second-budget
timings are **not** inference latency and must not support speed comparisons.
Runs were sequential, with no warmup or controlled host load. See run metadata.

Mean supplied semantic evidence rises from 2182.6 to 4598.7 tokens across the
24 questions. After coverage verification, four generation-only requests compare
the two previously failed questions with the old and new contexts, using the same
completed prompt and resolved `gpt-4.1-2025-04-14`. All four completed; no extra
judge calls were made.

Codex manually reviewed all four outputs against the same six required points
and exact supplied spans. The control supplies 4/6 facts and explicitly cannot
answer the other two because its evidence is missing. The new contexts supply
6/6 with supporting citations. The summer exception is stated, both CPT timing
statements retain their source attribution, and the answer does not invent how
the pages fit together. `manual-review.json` retains answer quotes, source quotes,
offsets and additional findings, including the control's misleading description
of its FAQ link excerpt and unsupported CPT acronym expansion.

This limited review is not v11, independent human review, or an exhaustive atomic
claim audit. Full-answer faithfulness, relevance and citation aggregate scores
are explicitly unavailable for this probe; expected-point support must not be
presented as those metrics.

| Generation-only observation (n=2 per variant) | Child / 4096 | Parent / 6144 |
| --- | ---: | ---: |
| First delta mean / P50 / P95, s | 1.210 / 1.210 / 1.635 | 0.923 / 0.923 / 1.040 |
| Completion mean / P50 / P95, s | 3.773 / 3.773 / 4.167 | 4.351 / 4.351 / 5.009 |
| Provider input tokens, total | 6636 | 12759 |
| Provider output tokens, total | 423 | 503 |

Two samples and uncontrolled provider variation cannot establish a latency gain.
These timings exclude retrieval, HTTP API transport and persistence. Actual
billing is unavailable; input token growth is observed, billed cost is not.
All metric statuses, errors, usage and raw deltas are preserved in the summary
and call files. The corpus/questions are familiar development data, not held-out
release accuracy. No further paid benchmark is required just to populate gaps.
