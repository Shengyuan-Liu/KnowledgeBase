"""Combine lexical and vector candidate ranks before parent expansion."""

from collections.abc import Sequence

from knowledgebase.config import DEFAULT_RRF_K, DEFAULT_RRF_LIMIT
from knowledgebase.schemas import BM25Match, FusedMatch, VectorMatch


def fuse_rrf(
    bm25_matches: Sequence[BM25Match],
    vector_matches: Sequence[VectorMatch],
    limit: int = DEFAULT_RRF_LIMIT,
    *,
    k: float = DEFAULT_RRF_K,
) -> list[FusedMatch]:
    """Fuse eligible candidate lists using equal-weight reciprocal rank fusion.

    BM25's rank field defines lexical order; vector distance defines vector order.
    Ties use chunk ID. Each route keeps its best occurrence of an ID, then assigns
    contiguous one-based ranks within that supplied route. A missing route adds
    zero. Raw scores are preserved for inspection, never added across routes.
    The fusion limit is applied after summing both routes, not before.

    Callers own eligibility filtering and route candidate limits. This function
    neither expands parents nor reads storage, modifies inputs, or calls models.
    """
    if limit <= 0:
        raise ValueError("limit must be positive.")
    if not 0 <= k < float("inf"):
        raise ValueError("k must be finite and nonnegative.")

    lexical = {}
    for match in sorted(bm25_matches, key=lambda item: (item.rank, item.chunk_id)):
        lexical.setdefault(match.chunk_id, match)
    vector = {}
    for match in sorted(vector_matches, key=lambda item: (item.distance, item.chunk_id)):
        vector.setdefault(match.chunk_id, match)

    candidates = {}
    for rank, match in enumerate(lexical.values(), start=1):
        candidates[match.chunk_id] = {
            "chunk_id": match.chunk_id,
            "rrf_score": 1 / (k + rank),
            "bm25_score": match.score,
            "bm25_rank": rank,
        }
    for rank, match in enumerate(vector.values(), start=1):
        candidate = candidates.setdefault(match.chunk_id, {
            "chunk_id": match.chunk_id, "rrf_score": 0.0,
        })
        candidate["rrf_score"] += 1 / (k + rank)
        candidate["vector_distance"] = match.distance
        candidate["vector_rank"] = rank

    ordered = sorted(candidates.values(), key=lambda item: (-item["rrf_score"], item["chunk_id"]))
    return [
        FusedMatch(**candidate, rank=rank)
        for rank, candidate in enumerate(ordered[:limit], start=1)
    ]
