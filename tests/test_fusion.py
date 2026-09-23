"""Rank-based fusion must preserve identities and separate incomparable scores."""

import pytest

from knowledgebase.rag.bm25 import search_bm25
from knowledgebase.rag.chunking import split_parent_child
from knowledgebase.rag.fusion import fuse_rrf
from knowledgebase.rag.parsing import parse_markdown
from knowledgebase.schemas import BM25Match, FusedMatch, VectorMatch


def lexical(chunk_id, rank, score=10.0):
    return BM25Match(chunk_id=chunk_id, rank=rank, score=score)


def vector(chunk_id, distance):
    return VectorMatch(chunk_id=chunk_id, distance=distance)


def test_shared_hit_sums_rank_contributions_and_preserves_route_scores():
    result = fuse_rrf([lexical("a", 1, 25), lexical("b", 2, 12)], [vector("b", 0.2), vector("c", 0.3)])
    assert [hit.chunk_id for hit in result] == ["b", "a", "c"]
    assert [hit.rank for hit in result] == [1, 2, 3]
    assert [hit.rrf_score for hit in result] == pytest.approx([0.0325224749, 0.0163934426, 0.0161290323])
    assert result[0].model_dump() == {
        "chunk_id": "b", "rank": 1, "rrf_score": pytest.approx(1 / 62 + 1 / 61),
        "bm25_score": 12.0, "bm25_rank": 2, "vector_distance": 0.2, "vector_rank": 1,
    }
    assert result[1].vector_rank is None and result[1].vector_distance is None
    assert result[2].bm25_rank is None and result[2].bm25_score is None
    assert FusedMatch.model_validate_json(result[0].model_dump_json()) == result[0]


@pytest.mark.parametrize(("bm25", "vectors", "ids"), [
    ([], [], []),
    ([lexical("b", 2), lexical("a", 1)], [], ["a", "b"]),
    ([], [vector("b", 0.2), vector("a", 0.1)], ["a", "b"]),
])
def test_empty_routes_and_single_route_ranking(bm25, vectors, ids):
    result = fuse_rrf(bm25, vectors)
    assert [hit.chunk_id for hit in result] == ids
    assert [hit.rrf_score for hit in result] == pytest.approx([1 / (60 + rank) for rank in range(1, len(ids) + 1)])


def test_scores_do_not_mix_and_monotonic_rescaling_does_not_change_fusion():
    bm25 = [lexical("a", 1, 100), lexical("b", 2, 3)]
    vectors = [vector("b", 0.1), vector("c", 0.9)]
    original = fuse_rrf(bm25, vectors)
    scaled = fuse_rrf(
        [match.model_copy(update={"score": match.score * 1000}) for match in bm25],
        [match.model_copy(update={"distance": match.distance * 2 + 10}) for match in vectors],
    )
    assert [(m.chunk_id, m.rrf_score, m.rank) for m in scaled] == [(m.chunk_id, m.rrf_score, m.rank) for m in original]
    assert scaled[0].bm25_score == 3000
    assert scaled[0].vector_distance == pytest.approx(10.2)


def test_bm25_rank_is_authoritative_even_when_raw_scores_disagree():
    result = fuse_rrf([lexical("a", 2, 1000), lexical("b", 1, 1)], [])
    assert [hit.chunk_id for hit in result] == ["b", "a"]


def test_duplicate_ids_contribute_once_per_route_and_do_not_consume_ranks():
    result = fuse_rrf(
        [lexical("a", 3, 1), lexical("b", 4, 2), lexical("a", 1, 10)],
        [vector("a", 0.9), vector("b", 0.2), vector("a", 0.1), vector("b", 0.3)],
    )
    assert [hit.chunk_id for hit in result] == ["a", "b"]
    assert [hit.rrf_score for hit in result] == pytest.approx([2 / 61, 2 / 62])
    assert result[0].bm25_score == 10 and result[0].vector_distance == 0.1
    assert result[1].bm25_rank == result[1].vector_rank == 2
    assert result[1].vector_distance == 0.2


def test_tied_route_and_fusion_scores_use_stable_chunk_ids():
    bm25 = [lexical("z", 1), lexical("a", 1)]
    vectors = [vector("z", 0.2), vector("a", 0.2)]
    result = fuse_rrf(bm25, vectors)
    assert [hit.chunk_id for hit in result] == ["a", "z"]
    assert result == fuse_rrf(bm25[::-1], vectors[::-1])
    # Reversed preferences give equal summed scores; final ties also use the ID.
    tied = fuse_rrf([lexical("z", 1), lexical("a", 2)], [vector("a", 0.1), vector("z", 0.2)])
    assert tied[0].rrf_score == tied[1].rrf_score
    assert [hit.chunk_id for hit in tied] == ["a", "z"]


def test_limit_applies_after_both_routes_have_contributed():
    result = fuse_rrf(
        [lexical("lexical-only", 1), lexical("shared", 2)],
        [vector("vector-only", 0.1), vector("shared", 0.2)],
        limit=1,
    )
    assert len(result) == 1 and result[0].chunk_id == "shared"
    assert result[0].bm25_rank == result[0].vector_rank == 2


def test_k_is_separate_from_limit_and_zero_is_supported():
    bm25 = [lexical("a", 1), lexical("b", 2)]
    vectors = [vector("b", 0.1)]
    result = fuse_rrf(bm25, vectors, limit=1, k=0)
    assert result[0].chunk_id == "b" and result[0].rrf_score == 1.5
    assert fuse_rrf(bm25, vectors, k=10)[0].rrf_score == pytest.approx(1 / 12 + 1 / 11)


@pytest.mark.parametrize("options", [{"limit": 0}, {"limit": -1}, {"k": -1}])
def test_invalid_fusion_parameters(options):
    with pytest.raises(ValueError):
        fuse_rrf([], [], **options)


def test_pure_bm25_and_rrf_composition_retains_distinct_children_of_one_parent():
    text = "# Setup\n\nInstall the SDK.\n\n```sh\nexport ANTHROPIC_API_KEY=placeholder\n```\n"
    hierarchy = split_parent_child(text, parse_markdown(text), "guide", parent_max_tokens=128, child_max_tokens=32, encoding_name="cl100k_base")
    assert len(hierarchy.parents) == 1 and len(hierarchy.children) == 2
    bm25 = search_bm25("ANTHROPIC_API_KEY", hierarchy.children)
    vectors = [vector(child.chunk_id, 0.1 + i * 0.1) for i, child in enumerate(hierarchy.children)]
    before = [match.model_dump() for match in bm25], [match.model_dump() for match in vectors], hierarchy.model_dump()
    result = fuse_rrf(bm25, vectors)
    assert result[0].chunk_id == bm25[0].chunk_id
    assert {hit.chunk_id for hit in result} == {child.chunk_id for child in hierarchy.children}
    assert not {hit.chunk_id for hit in result}.intersection(parent.parent_id for parent in hierarchy.parents)
    assert before == ([match.model_dump() for match in bm25], [match.model_dump() for match in vectors], hierarchy.model_dump())
