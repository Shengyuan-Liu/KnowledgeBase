"""Check identity, bounded scoring, reproducible inputs, and independent ranks."""

import json
from unittest.mock import Mock

import pytest
import tiktoken

from knowledgebase.rag.reranking import build_rerank_messages, rerank
from knowledgebase.schemas import FusedMatch, RelevanceScore, RerankCandidate, RerankResult


def candidate(identity, rank, text="Exact source text.", heading=None):
    return RerankCandidate(
        chunk_id=identity, rank=rank, rrf_score=1 / (60 + rank),
        bm25_score=2.3, bm25_rank=rank, vector_distance=None, vector_rank=None,
        text=text, heading_path=heading or [],
    )


def scorer(scores):
    client = Mock(model="offline-reranker")
    client.score.return_value = [RelevanceScore(chunk_id=identity, score=score) for identity, score in scores]
    return client


def test_scores_map_by_identity_and_preserve_exact_input_and_route_metadata():
    inputs = [candidate("a", 1, "See the admissions page."),
              candidate("b", 2, "  GPA ≥ 3.0.\r\nComplete 66% of credits.\n", ["Academic progress"])]
    original = [item.model_dump() for item in inputs]
    client = scorer([("b", 3), ("a", 1)])
    result = rerank("What academic progress requirements apply?", inputs, client, top_k=1)
    assert [hit.chunk_id for hit in result.matches] == ["b", "a"]
    assert [hit.rerank_rank for hit in result.matches] == [1, 2]
    assert [hit.rank for hit in result.matches] == [2, 1]
    assert [hit.rerank_score for hit in result.matches] == [3, 1]
    assert result.selected == result.matches[:1]
    assert result.matches[0].model_dump(include=set(FusedMatch.model_fields)) == inputs[1].model_dump(include=set(FusedMatch.model_fields))
    assert [item.model_dump() for item in inputs] == original
    restored = RerankResult.model_validate_json(result.model_dump_json())
    assert restored == result
    assert restored.selected == result.selected
    messages = client.score.call_args.args[0]
    body = json.loads(messages[1]["content"])
    assert body == {"question": result.question, "candidates": [
        {"chunk_id": item.chunk_id, "text": item.text, "heading_path": item.heading_path}
        for item in inputs
    ]}
    assert messages == build_rerank_messages(restored.question, restored.candidates)
    assert "rrf_score" not in messages[1]["content"]


def test_score_window_is_selected_by_rrf_rank_before_the_model_call():
    inputs = [candidate("c", 3), candidate("b", 2), candidate("a", 1)]
    client = scorer([("b", 3), ("a", 0)])
    result = rerank("Question", inputs, client, top_k=1, candidate_limit=2)
    assert [item.chunk_id for item in result.candidates] == ["a", "b"]
    assert [hit.chunk_id for hit in result.selected] == ["b"]
    assert len(result.matches) == 2
    assert "c" not in [item["chunk_id"] for item in json.loads(client.score.call_args.args[0][1]["content"])["candidates"]]


def test_ties_use_rrf_rank_then_stable_child_identity_and_keep_siblings():
    inputs = [candidate("parent:child:2", 2), candidate("parent:child:1", 2), candidate("other:child:0", 1)]
    client = scorer([(item.chunk_id, 3) for item in inputs])
    result = rerank("Question", inputs, client)
    assert [hit.chunk_id for hit in result.matches] == ["other:child:0", "parent:child:1", "parent:child:2"]


def test_empty_candidates_do_not_call_model():
    client = scorer([])
    result = rerank("Question", [], client)
    assert result.candidates == result.matches == result.selected == []
    assert result.input_tokens == 0
    client.score.assert_not_called()


def test_input_budget_counts_exact_messages_and_never_truncates():
    inputs = [candidate("a", 1, "café\r\n<|endoftext|>\n", ["Heading"])]
    messages = build_rerank_messages("Question", inputs)
    encoding = tiktoken.get_encoding("o200k_base")
    tokens = sum(len(encoding.encode_ordinary(m["content"])) for m in messages)
    client = scorer([("a", 2)])
    result = rerank("Question", inputs, client, max_input_tokens=tokens, encoding_name="o200k_base")
    assert result.input_tokens == tokens
    assert result.tokenizer == "o200k_base"
    client.score.assert_called_once_with(messages, ["a"])
    client.reset_mock()
    with pytest.raises(ValueError, match="no text was truncated"):
        rerank("Question", inputs, client, max_input_tokens=tokens - 1, encoding_name="o200k_base")
    client.score.assert_not_called()


@pytest.mark.parametrize("scores", [[], [("a", 3)], [("a", 3), ("a", 2)], [("a", 3), ("unknown", 2)]])
def test_every_scored_id_must_match_exactly_one_input_without_fallback(scores):
    client = scorer(scores)
    with pytest.raises(ValueError, match="every supplied chunk ID exactly once"):
        rerank("Question", [candidate("a", 1), candidate("b", 2)], client)
    assert client.score.call_count == 1


def test_provider_failure_propagates_without_repair_or_rrf_fallback():
    client = scorer([])
    client.score.side_effect = RuntimeError("Provider failed")
    with pytest.raises(RuntimeError, match="Provider failed"):
        rerank("Question", [candidate("a", 1)], client)
    assert client.score.call_count == 1


@pytest.mark.parametrize("options", [{"top_k": 0}, {"candidate_limit": 0}, {"max_input_tokens": 0}])
def test_limits_are_positive(options):
    with pytest.raises(ValueError, match="must be positive"):
        rerank("Question", [], scorer([]), **options)


def test_duplicate_candidate_identity_is_rejected_before_scoring():
    client = scorer([])
    with pytest.raises(ValueError, match="IDs must be unique"):
        rerank("Question", [candidate("a", 1), candidate("a", 2)], client)
    client.score.assert_not_called()
