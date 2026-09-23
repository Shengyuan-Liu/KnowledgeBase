# Reciprocal Rank Fusion

Status: implemented as a pure function on `v1` and connected to the default
[hybrid retrieval service](hybrid-retrieval.md) in API, CLI, and evaluations.
User acceptance and merge approval remain separate.

## Interface

```python
from knowledgebase.rag.fusion import fuse_rrf
from knowledgebase.schemas import BM25Match, VectorMatch

lexical = [
    BM25Match(chunk_id="a", score=25.0, rank=1),
    BM25Match(chunk_id="b", score=12.0, rank=2),
]
vector = [
    VectorMatch(chunk_id="b", distance=0.2),
    VectorMatch(chunk_id="c", distance=0.3),
]
fused = fuse_rrf(lexical, vector, limit=20, k=60)
assert [hit.chunk_id for hit in fused] == ["b", "a", "c"]
```

Each `FusedMatch` has:

| Field | Meaning |
| --- | --- |
| `chunk_id` | Original child or legacy flat-chunk identity |
| `rrf_score` | Sum of contributions from the routes that contain the ID |
| `rank` | One-based position in the final fused list |
| `bm25_score`, `bm25_rank` | Selected lexical score and deduplicated route rank; null when absent |
| `vector_distance`, `vector_rank` | Selected vector distance and deduplicated route rank; null when absent |

The returned ID is never replaced with a parent ID. Two children sharing a parent
remain separate candidates. Parent expansion and deduplication occur later.
No source text is copied or modified by fusion, and the input objects are unchanged.

## Ranking Rules

1. Sort BM25 candidates by their explicit `rank`, breaking ties by chunk ID.
   BM25 rank is authoritative; its raw score is retained for inspection.
2. Sort vector candidates by increasing distance, breaking ties by chunk ID.
3. Within each route, retain the first/best occurrence of each chunk ID. Then
   assign contiguous ranks starting at one. Repeated IDs cannot inflate the
   score or consume positions. If supplied BM25 ranks have gaps, the ranks used
   for fusion are compacted within this supplied candidate list.
4. For each ID, add `1 / (k + route_rank)` from each route where it appears.
   A missing route contributes zero. The two routes have equal weight.
5. Sort by decreasing RRF score, breaking ties by chunk ID. Only then apply the
   fusion `limit` and assign contiguous final ranks.

For `b` above, the score is `1/62 + 1/61`, because its lexical rank is 2 and vector
rank is 1. A single-route candidate contributes only its one reciprocal rank.
An empty route is supported; two empty routes return `[]`.

This is the rank-based formula from the
[original RRF paper](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf).
The default `k=60` follows that paper's setting; it is not a measured optimum for
this library. Increasing BM25 score magnitudes or rescaling vector distances
without changing their ordering does not increase their weight in fusion.

Raw BM25 scores, cosine distances, and RRF scores remain separate. None is a
probability of answer correctness. A consensus between two irrelevant routes can
still outrank a relevant single-route result.

## Limits and Responsibilities

`DEFAULT_RRF_K=60` and `DEFAULT_RRF_LIMIT=20` are centralized in
[`config.py`](../knowledgebase/config.py). The fusion window is an experimental
starting value for this standalone function. Both are explicit parameters. The
service uses `RRF_K`, takes `RETRIEVAL_CANDIDATE_LIMIT` hits from each route, saves
the full fused union, and selects `RETRIEVAL_TOP_K` children before expansion. `k` must be finite and nonnegative and
`limit` must be positive. `k=0` is supported.

The caller is responsible for selecting eligible files and limiting each route
before passing candidates in. Fusion cannot determine whether an ID belongs to a
Ready, deleted, or failed file. Keep the route limits, RRF constant, fusion window,
later rerank/selection limit, and final evidence-token budget distinct.

This module does not query Chroma or SQLite, rebuild an index, invoke providers,
expand parents, rerank text, or select evidence according to its token budget.
It uses only the standard library and existing schemas.

## Verification

Run `uv run --locked python -m pytest tests/test_fusion.py` or `make test`.
The tests cover hand-calculated contributions, separate score metadata, empty and
single routes, raw-score rescaling, authoritative BM25 rank, duplicate IDs,
stable tie-breaking, post-fusion limiting, explicit constants, serialization,
and composition with real BM25 output while retaining separate sibling children.

The [offline recorded-candidate replay](../evals/analyses/2026-09-23-rrf-standalone.md)
inspects the original GPA and CPT failures and the Markdown setup case. It does
not generate new answers or prove that final parent evidence will fit the budget.
