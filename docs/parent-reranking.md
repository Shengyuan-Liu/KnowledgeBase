# Optional Parent Reranking

`RERANK_UNIT=parent` scores complete parent regions instead of isolated children.
It is an opt-in query-time control for the observed case where several short
semantic children from one region consume the selected-hit limit, or a candidate
child does not itself contain the relevant surrounding rule. The default remains
`RERANK_UNIT=child`; no reindexing is required.

After BM25/vector fusion, group candidates by parent in RRF order. Keep the first
child as each parent's representative, then apply `RERANK_CANDIDATE_LIMIT` to those
unique regions. Send the exact parent text and heading to the local reranker.
Keep the representative child's route ranks and ID, record `scoring_parent_id`
on the scored input and result, and retain every scoring input and score in the
saved diagnostics. Flat chunks continue to score their own text.

Top K selects representative children for distinct regions. Evidence packing is
unchanged: whole parents first, then complete representative children where a
parent does not fit. A high parent score therefore does not guarantee that its
entire content reaches generation. Inspect final evidence and budget exclusions.
The representative child is the best RRF hit, not necessarily the sentence that
supports the answer; the score is explicitly a parent score.

Whole-parent scoring costs more local compute and requires appropriate limits.
The acceptance experiment uses pair limit 2048 and total input limit 32768 for
1536-token parents. Tokenizers differ; these are measured experiment settings,
not guarantees for arbitrary content. Oversized input still fails explicitly;
there is no truncation or automatic fallback. Set these through `.env`:

```dotenv
RERANK_ENABLED=true
RERANK_UNIT=parent
RERANK_MAX_PAIR_TOKENS=2048
RERANK_MAX_INPUT_TOKENS=32768
```

The [acceptance plan](../evals/library-runs/20260925-parent-reranking/PLAN.md)
compares both 4096 and 6144 evidence-token budgets. Higher evidence budgets are a
separate quality, latency and token-usage tradeoff; defaults are unchanged.
Semantic chunking remains experimental. This option does not guarantee coverage
of every part of an arbitrary question.
