import pytest

from knowledgebase.rag.citations import validate_citations
from knowledgebase.schemas import AnswerSource, CitationCheck


def source(number):
    return AnswerSource(source_id=number, file_id="file-1", file_name="notes.txt",
                        chunk_id=f"file-1:{number}", text="An excerpt.", distance=.1)


def test_checks_actual_ids_and_deduplicates_in_first_appearance_order():
    text = "Third [3], first [1][3], unavailable [5][0][5], and second [2]."
    result = validate_citations(text, [source(1), source(3)])
    assert result == CitationCheck(valid_source_ids=[3, 1], invalid_source_ids=[5, 0, 2], no_citations=False)


def test_ids_are_scoped_to_the_current_answer():
    text = "A claim. [2]"
    assert validate_citations(text, [source(1), source(2)]).valid_source_ids == [2]
    assert validate_citations(text, [source(1)]).invalid_source_ids == [2]
    assert validate_citations(text, []).invalid_source_ids == [2]


@pytest.mark.parametrize("text", [
    "There is not enough information in the provided sources to answer this question.",
    "A factual statement without a citation.",
    "", "Unrecognized syntax [1, 2] and [1-3] and [notes].",
])
def test_no_recognized_citations_is_reported_without_a_quality_verdict(text):
    assert validate_citations(text, [source(1)]) == CitationCheck(
        valid_source_ids=[], invalid_source_ids=[], no_citations=True,
    )


def test_number_existence_does_not_check_whether_the_excerpt_supports_the_claim():
    result = validate_citations("The moon is made of cheese. [1]", [source(1)])
    assert result.valid_source_ids == [1]
    assert result.invalid_source_ids == []
