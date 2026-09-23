"""Lexical scoring, corpus-specific tokenization, and standalone child identity."""

from pathlib import Path

import pytest

from knowledgebase.rag.bm25 import search_bm25, tokenize
from knowledgebase.rag.chunking import split_parent_child
from knowledgebase.rag.parsing import parse_markdown, parse_txt
from knowledgebase.schemas import BM25Match, Chunk


def chunk(chunk_id, text):
    return Chunk(chunk_id=chunk_id, file_id=chunk_id, text=text, index=0, start_offset=0, end_offset=len(text))


@pytest.mark.parametrize(("text", "expected"), [
    ("GPA gpa GpA", ["gpa", "gpa", "gpa"]),
    ("DS-GA 1002 / DS GA 1002 / DS–GA–1002", ["ds", "ga", "1002"] * 3),
    (r"ANTHROPIC_API_KEY tool\_choice", ["anthropic", "api", "key", "tool", "choice"]),
    ("GPA >= 3.0; complete 66% of credits.", ["gpa", "3.0", "complete", "66", "of", "credits"]),
    ("```python\nclient.messages.create()\n```", ["python", "client", "messages", "create"]),
    ("The café closes.\r\n", ["the", "café", "closes"]),
    ("--- ** | 🙂", []),
])
def test_tokenize_actual_document_terms(text, expected):
    assert tokenize(text) == expected


def test_scores_match_hand_calculated_reference_and_exclude_nonmatches():
    # Three length-2 documents; apple appears in two. IDF = ln(1.6).
    documents = [chunk("twice", "apple apple"), chunk("once", "apple pear"), chunk("other", "pear banana")]
    result = search_bm25("apple", documents, top_k=10)
    assert [r.chunk_id for r in result] == ["twice", "once"]
    assert [r.rank for r in result] == [1, 2]
    assert [r.score for r in result] == pytest.approx([0.6462549902, 0.4700036292])
    assert BM25Match.model_validate_json(result[0].model_dump_json()) == result[0]


def test_length_normalization_and_explicit_b_override():
    documents = [chunk("a-long", "GPA " + "other " * 20), chunk("z-short", "GPA")]
    assert search_bm25("gpa", documents)[0].chunk_id == "z-short"
    result = search_bm25("gpa", documents, b=0)
    assert result[0].score == result[1].score
    assert [r.chunk_id for r in result] == ["a-long", "z-short"]


def test_rare_terms_outweigh_common_terms_at_equal_length():
    documents = [chunk("a", "common filler"), chunk("b", "common filler"), chunk("c", "rare filler")]
    assert search_bm25("common rare", documents)[0].chunk_id == "c"


def test_query_repetition_does_not_reweight_terms_and_ties_ignore_input_order():
    documents = [chunk("z", "GPA 3.0"), chunk("a", "GPA 3.0")]
    expected = search_bm25("gpa 3.0", documents)
    assert search_bm25("3.0 GPA GPA", documents[::-1]) == expected
    assert search_bm25("gpa 3.0", documents, top_k=1) == expected[:1]
    assert [r.chunk_id for r in expected] == ["a", "z"]


def test_common_terms_and_one_document_still_produce_positive_hits():
    result = search_bm25("GPA", [chunk("only", "GPA")])
    assert len(result) == 1 and result[0].score > 0
    assert result[0].rank == 1


@pytest.mark.parametrize(("question", "documents"), [
    ("GPA", []), ("GPA", [chunk("punctuation", "---")]),
    ("", [chunk("a", "GPA")]), ("?!", [chunk("a", "GPA")]),
    ("scholarships", [chunk("a", "GPA")]),
])
def test_empty_or_unmatched_search_returns_no_padding(question, documents):
    assert search_bm25(question, documents) == []


def test_tokenless_chunks_do_not_distort_corpus_statistics():
    document = chunk("one", "GPA")
    assert search_bm25("GPA", [document, chunk("rule", "---")]) == search_bm25("GPA", [document])


@pytest.mark.parametrize("settings", [{"top_k": 0}, {"k1": -1}, {"b": -0.1}, {"b": 1.1}])
def test_invalid_search_parameters(settings):
    with pytest.raises(ValueError):
        search_bm25("GPA", [], **settings)


def test_search_returns_child_identity_without_expanding_or_modifying_sources():
    text = "# API\n\nSet ANTHROPIC_API_KEY.\n\n```python\nclient.messages.create()\n```\n"
    hierarchy = split_parent_child(text, parse_markdown(text), "api", parent_max_tokens=128, child_max_tokens=32, encoding_name="cl100k_base")
    original = hierarchy.model_dump()
    result = search_bm25("anthropic api key", hierarchy.children)
    assert result
    ids = {child.chunk_id for child in hierarchy.children}
    assert all(hit.chunk_id in ids for hit in result)
    assert not {hit.chunk_id for hit in result}.intersection(p.parent_id for p in hierarchy.parents)
    assert hierarchy.model_dump() == original


def test_rebuilding_from_changed_input_does_not_retain_removed_chunks():
    a, b = chunk("a", "GPA"), chunk("b", "CPT")
    assert search_bm25("GPA", [a, b])[0].chunk_id == "a"
    assert search_bm25("GPA", [b]) == []
    replacement = chunk("new", "GPA")
    assert [hit.chunk_id for hit in search_bm25("GPA", [b, replacement])] == ["new"]


def test_frozen_faq_numeric_and_course_queries_find_exact_supporting_child():
    source = Path(__file__).resolve().parents[1] / "evals/materials/nyu/msds/masters-in-data-science-faq-general.txt"
    text = source.read_text()
    children = split_parent_child(text, parse_txt(text), "faq", parent_max_tokens=1536, child_max_tokens=512, encoding_name="cl100k_base").children
    by_id = {child.chunk_id: child for child in children}
    for query, phrase in [
        ("minimum GPA 3.0 66%", "minimum GPA of 3.0"),
        ("DS GA 1002 waived transcripts syllabi", "only DS-GA 1002 may be waived"),
    ]:
        hit = search_bm25(query, children, top_k=1)[0]
        assert phrase in by_id[hit.chunk_id].text
