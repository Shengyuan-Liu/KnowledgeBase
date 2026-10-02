from pathlib import Path

import pytest
import tiktoken

from knowledgebase.rag.chunking import split_structured
from knowledgebase.rag.parsing import parse_markdown, parse_txt


@pytest.fixture(scope="module")
def encoding():
    return tiktoken.get_encoding("cl100k_base")


def count(text, encoding):
    return len(encoding.encode_ordinary(text))


def split(text, budget, *, markdown=False):
    blocks = parse_markdown(text) if markdown else parse_txt(text)
    chunks = split_structured(
        text, blocks, "file-1", max_tokens=budget, encoding_name="cl100k_base",
    )
    return blocks, chunks


def assert_chunk_contract(text, blocks, chunks, budget, encoding):
    previous_end = 0
    for index, chunk in enumerate(chunks):
        assert previous_end <= chunk.start_offset < chunk.end_offset <= len(text)
        assert not text[previous_end:chunk.start_offset].strip()
        assert chunk.text == text[chunk.start_offset:chunk.end_offset]
        assert chunk.token_count == count(chunk.text, encoding) <= budget
        assert chunk.max_tokens == budget
        assert chunk.tokenizer == encoding.name
        assert chunk.index == index
        assert chunk.file_id == "file-1"
        assert chunk.source_block_indices == [
            i for i, block in enumerate(blocks)
            if block.start_offset < chunk.end_offset and block.end_offset > chunk.start_offset
        ]
        assert all(
            list(blocks[i].heading_path) == chunk.heading_path for i in chunk.source_block_indices
        )
        previous_end = chunk.end_offset
    assert not text[previous_end:].strip()
    assert len({chunk.chunk_id for chunk in chunks}) == len(chunks)


@pytest.mark.parametrize("text", ["", " \r\n\t "])
def test_empty_source_has_no_chunks(text):
    assert split(text, 32)[1] == []


@pytest.mark.parametrize("budget", [0, -1])
def test_token_limit_must_be_positive(budget):
    with pytest.raises(ValueError, match="max_tokens must be positive"):
        split("Text.", budget)


def test_adjacent_short_paragraphs_merge_with_their_heading(encoding):
    text = "# Guide\n\nFirst paragraph.\n\nSecond paragraph.\n"
    blocks, chunks = split(text, 64, markdown=True)

    assert len(chunks) == 1
    assert chunks[0].text == text
    assert chunks[0].heading_path == ["Guide"]
    assert chunks[0].source_block_indices == [0, 1, 2]
    assert_chunk_contract(text, blocks, chunks, 64, encoding)


def test_new_heading_is_a_boundary_even_when_its_label_repeats(encoding):
    text = "# Guide\n\nFirst.\n\n# Guide\n\nSecond.\n\n## Setup\n\nThird.\n"
    blocks, chunks = split(text, 100, markdown=True)

    assert len(chunks) == 3
    assert [chunk.heading_path for chunk in chunks] == [["Guide"], ["Guide"], ["Guide", "Setup"]]
    assert [chunk.source_block_indices for chunk in chunks] == [[0, 1], [2, 3], [4, 5]]
    assert_chunk_contract(text, blocks, chunks, 100, encoding)


def test_separator_tokens_are_included_in_the_merge_budget(encoding):
    text = "Hello\n\nWorld"
    blocks = parse_txt(text)
    budget = sum(count(block.text, encoding) for block in blocks)
    # Use a larger blank separator to make separate block counts underestimate the slice.
    text = "Hello\n" + "\n \n" * 20 + "World"
    blocks, chunks = split(text, budget)

    assert len(chunks) == 2
    assert_chunk_contract(text, blocks, chunks, budget, encoding)


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_wrapped_sentences_split_at_sentence_ends_not_line_wraps(newline, encoding):
    first = f"The first sentence wraps{newline}onto another line. "
    second = "A second sentence follows."
    text = first + second
    budget = max(count(first, encoding), count(second, encoding))
    blocks, chunks = split(text, budget)

    assert [chunk.text for chunk in chunks] == [first, second]
    assert_chunk_contract(text, blocks, chunks, budget, encoding)


def test_abbreviations_versions_and_decimals_do_not_create_sentence_fragments(encoding):
    first = "Dr. Smith uses v1.2 at a cost of $3.50. "
    second = "The next step is documented separately."
    text = first + second
    budget = max(count(first, encoding), count(second, encoding))
    blocks, chunks = split(text, budget)

    assert [chunk.text for chunk in chunks] == [first, second]
    assert_chunk_contract(text, blocks, chunks, budget, encoding)


def test_long_sentence_prefers_clause_boundaries_before_words(encoding):
    clauses = ["Install the application first; ", "configure the local database next; ", "start the server last."]
    text = "".join(clauses)
    budget = max(count(clause, encoding) for clause in clauses)
    blocks, chunks = split(text, budget)

    assert [chunk.text for chunk in chunks] == clauses
    assert_chunk_contract(text, blocks, chunks, budget, encoding)


def test_long_sentence_without_clauses_splits_between_words(encoding):
    words = ["configure", "the", "application", "with", "a", "local", "database", "before", "starting", "the", "server"]
    text = " ".join(words)
    blocks, chunks = split(text, 4)

    assert len(chunks) > 1
    assert [word for chunk in chunks for word in chunk.text.split()] == words
    assert_chunk_contract(text, blocks, chunks, 4, encoding)


def test_small_budget_keeps_fitting_words_whole_despite_whitespace(encoding):
    text = "hello world "
    blocks, chunks = split(text, 1)

    assert [chunk.text for chunk in chunks] == ["hello", "world"]
    assert_chunk_contract(text, blocks, chunks, 1, encoding)


@pytest.mark.parametrize("word", ["abcdefghij" * 20, "café🙂" * 20])
def test_oversized_indivisible_word_splits_without_changing_unicode(word, encoding):
    blocks, chunks = split(word, 8)

    assert len(chunks) > 1
    assert "".join(chunk.text for chunk in chunks) == word
    assert_chunk_contract(word, blocks, chunks, 8, encoding)


def test_budget_too_small_for_a_unicode_character_is_explicit():
    with pytest.raises(ValueError, match="one source character"):
        split("🙂", 1)


def test_code_stays_separate_from_prose_and_splits_only_between_fitting_lines(encoding):
    lines = ["```python\n", "print('first example')\n", "print('second example')\n", "```\n"]
    code = "".join(lines)
    text = "# Guide\n\nBefore.\n\n" + code + "\nAfter."
    budget = max(count(line, encoding) for line in lines)
    blocks, chunks = split(text, budget, markdown=True)
    code_index = next(i for i, block in enumerate(blocks) if block.kind == "code")
    code_chunks = [chunk for chunk in chunks if code_index in chunk.source_block_indices]
    line_ends = {sum(map(len, lines[:i])) for i in range(1, len(lines) + 1)}

    assert len(code_chunks) > 1
    assert "".join(chunk.text for chunk in code_chunks) == code
    assert all(chunk.source_block_indices == [code_index] for chunk in code_chunks)
    assert all(chunk.end_offset - blocks[code_index].start_offset in line_ends for chunk in code_chunks)
    assert_chunk_contract(text, blocks, chunks, budget, encoding)


def test_table_rows_stay_whole_without_synthetic_headers(encoding):
    rows = ["| Name | Value |\n", "| --- | --- |\n", "| First | One |\n", "| Second | Two |\n"]
    text = "".join(rows)
    budget = max(count(row, encoding) for row in rows)
    blocks, chunks = split(text, budget, markdown=True)

    assert [chunk.text for chunk in chunks] == rows
    assert all(chunk.source_block_indices == [0] for chunk in chunks)
    assert_chunk_contract(text, blocks, chunks, budget, encoding)


def test_list_keeps_nested_content_with_its_fitting_item(encoding):
    first = "- First step\n  - Nested detail\n"
    second = "- Second step with explanation\n"
    text = first + second
    budget = max(count(first, encoding), count(second, encoding))
    blocks, chunks = split(text, budget, markdown=True)

    assert [chunk.text for chunk in chunks] == [first, second]
    assert_chunk_contract(text, blocks, chunks, budget, encoding)


def test_long_code_line_still_respects_the_hard_limit(encoding):
    text = "```text\n" + "long_identifier_" * 50 + "\n```\n"
    blocks, chunks = split(text, 12, markdown=True)

    assert len(chunks) > 1
    assert_chunk_contract(text, blocks, chunks, 12, encoding)


def test_literal_special_token_strings_are_ordinary_document_content(encoding):
    text = "The literal marker <|endoftext|> appears in this document."
    blocks, chunks = split(text, 16)

    assert_chunk_contract(text, blocks, chunks, 16, encoding)


def test_ids_and_settings_are_repeatable_and_file_specific():
    text = "First paragraph.\n\nSecond paragraph."
    blocks = parse_txt(text)
    kwargs = dict(max_tokens=8, encoding_name="cl100k_base")
    first = split_structured(text, blocks, "file-1", **kwargs)

    assert first == split_structured(text, blocks, "file-1", **kwargs)
    other = split_structured(text, blocks, "file-2", **kwargs)
    assert {chunk.chunk_id for chunk in first}.isdisjoint(chunk.chunk_id for chunk in other)


@pytest.mark.parametrize("budget", [32, 128])
def test_frozen_deepseek_corpus_respects_spans_structure_and_token_limit(budget, encoding):
    corpus = Path(__file__).resolve().parents[1] / "evals/materials/deepseek/md"
    paths = sorted(corpus.rglob("*.md"))
    assert paths
    for path in paths:
        text = path.read_bytes().decode("utf-8")
        blocks, chunks = split(text, budget, markdown=True)
        assert_chunk_contract(text, blocks, chunks, budget, encoding)
