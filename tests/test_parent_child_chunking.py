from pathlib import Path

import pytest
import tiktoken

from knowledgebase.rag.chunking import split_parent_child
from knowledgebase.rag.parsing import parse_markdown, parse_txt
from knowledgebase.schemas import ParentChildChunks


def split(text, parent_budget=64, child_budget=16, *, markdown=True, tokenizer="cl100k_base"):
    blocks = parse_markdown(text) if markdown else parse_txt(text)
    result = split_parent_child(
        text, blocks, "file-1", parent_max_tokens=parent_budget,
        child_max_tokens=child_budget, encoding_name=tokenizer,
    )
    return blocks, result


def assert_contract(text, blocks, result, parent_budget, child_budget, tokenizer="cl100k_base"):
    encoding = tiktoken.get_encoding(tokenizer)
    for regions, budget in [(result.parents, parent_budget), (result.children, child_budget)]:
        previous_end = 0
        for index, region in enumerate(regions):
            assert previous_end <= region.start_offset < region.end_offset <= len(text)
            assert not text[previous_end:region.start_offset].strip()
            assert region.text == text[region.start_offset:region.end_offset]
            assert region.token_count == len(encoding.encode_ordinary(region.text)) <= budget
            assert region.max_tokens == budget
            assert region.tokenizer == tokenizer
            assert region.file_id == "file-1"
            assert region.index == index
            assert region.source_block_indices == [
                i for i, block in enumerate(blocks)
                if block.start_offset < region.end_offset and block.end_offset > region.start_offset
            ]
            assert all(blocks[i].heading_path == region.heading_path for i in region.source_block_indices)
            previous_end = region.end_offset
        assert not text[previous_end:].strip()

    parents = {parent.parent_id: parent for parent in result.parents}
    assert len(parents) == len(result.parents)
    assert len({child.chunk_id for child in result.children}) == len(result.children)
    assert set(parents).isdisjoint(child.chunk_id for child in result.children)
    assert {child.parent_id for child in result.children} == set(parents)
    for child in result.children:
        parent = parents[child.parent_id]
        assert parent.start_offset <= child.start_offset < child.end_offset <= parent.end_offset
        assert child.heading_path == parent.heading_path
        assert set(child.source_block_indices) <= set(parent.source_block_indices)
        assert child.text == parent.text[
            child.start_offset - parent.start_offset:child.end_offset - parent.start_offset
        ]


@pytest.mark.parametrize("text", ["", " \r\n\t"])
def test_empty_input_has_no_parents_or_children(text):
    _, result = split(text)
    assert result == ParentChildChunks(parents=[], children=[])


@pytest.mark.parametrize("parent_budget,child_budget", [(0, 8), (32, 0), (-1, 8), (32, -1)])
def test_both_budgets_must_be_positive(parent_budget, child_budget):
    with pytest.raises(ValueError, match="must be positive"):
        split("Text.", parent_budget, child_budget)


def test_child_budget_cannot_exceed_parent_budget():
    with pytest.raises(ValueError, match="must not exceed"):
        split("Text.", 8, 16)


def test_one_parent_retains_prose_list_code_and_table_context():
    text = (
        "# Setup\n\nRead the instructions first.\n\n"
        "- Install the package.\n- Create the database.\n\n"
        "```python\nprint('ready')\n```\n\n"
        "| Option | Value |\n| --- | --- |\n| retries | 2 |\n\n"
        "Restart after changing the configuration.\n"
    )
    blocks, result = split(text, 256, 24)
    assert len(result.parents) == 1
    assert result.parents[0].text == text
    assert result.parents[0].source_block_indices == list(range(len(blocks)))
    assert len(result.children) >= 5
    for kind in ("list", "code", "table"):
        index = next(i for i, block in enumerate(blocks) if block.kind == kind)
        assert all(c.source_block_indices == [index] for c in result.children if index in c.source_block_indices)
    assert_contract(text, blocks, result, 256, 24)


def test_preamble_repeated_headings_and_nested_sections_remain_separate():
    text = "Preamble.\n\n# Guide\n\nFirst.\n\n## Setup\n\nInstall.\n\n## Setup\n\nRestart.\n\n# Next\n\nLast."
    blocks, result = split(text, 128, 32)
    assert [p.heading_path for p in result.parents] == [[], ["Guide"], ["Guide", "Setup"], ["Guide", "Setup"], ["Next"]]
    assert [p.source_block_indices for p in result.parents] == [[0], [1, 2], [3, 4], [5, 6], [7, 8]]
    assert_contract(text, blocks, result, 128, 32)


def test_oversized_txt_paragraph_splits_parents_and_children_at_fitting_sentences():
    sentences = [f"Sentence number {i} describes a complete step. " for i in range(12)]
    text = "".join(sentences)
    encoding = tiktoken.get_encoding("cl100k_base")
    child_budget = max(len(encoding.encode_ordinary(s)) for s in sentences)
    parent_budget = child_budget * 3
    blocks, result = split(text, parent_budget, child_budget, markdown=False)
    assert len(result.parents) > 1
    assert len(result.children) > len(result.parents)
    assert [c.text for c in result.children] == sentences
    assert_contract(text, blocks, result, parent_budget, child_budget)


@pytest.mark.parametrize("kind,text", [
    ("code", "```python\n" + "print('long example')\n" * 12 + "```\n"),
    ("table", "| Name | Value |\n| --- | --- |\n" + "| First | One |\n" * 12),
    ("list", "- First step\n  - Nested detail\n" * 12),
])
def test_large_structural_blocks_keep_fitting_lines_and_global_associations(kind, text):
    blocks, result = split(text, 32, 16)
    assert len(blocks) == 1 and blocks[0].kind == kind
    assert len(result.parents) > 1
    assert all(c.source_block_indices == [0] for c in result.children)
    offset = 0
    for line in text.splitlines(keepends=True):
        assert any(c.start_offset <= offset and c.end_offset >= offset + len(line) for c in result.children)
        offset += len(line)
    assert_contract(text, blocks, result, 32, 16)


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_unicode_source_and_original_offsets_survive_both_levels(newline):
    text = newline.join(["# Café 🙂", "", "A wrapped sentence continues", "on the next line. Another sentence follows.", "", "## Next", "", "Café closes early. 🙂", ""])
    blocks, result = split(text, 24, 12)
    assert_contract(text, blocks, result, 24, 12)


def test_oversized_indivisible_word_preserves_every_character():
    text = "café🙂" * 60
    blocks, result = split(text, 16, 8, markdown=False)
    assert "".join(p.text for p in result.parents) == text
    assert "".join(c.text for c in result.children) == text
    assert_contract(text, blocks, result, 16, 8)


def test_separator_whitespace_counts_toward_parent_limit():
    text = "Hello\n" + "\n \n" * 20 + "World"
    blocks, result = split(text, 3, 1, markdown=False)
    assert [p.text.strip() for p in result.parents] == ["Hello", "World"]
    assert_contract(text, blocks, result, 3, 1)


def test_equal_budgets_and_selected_tokenizer_are_supported():
    text = "# Guide\n\nKeep this small paragraph intact.\n"
    blocks, result = split(text, 32, 32, tokenizer="o200k_base")
    assert len(result.parents) == len(result.children) == 1
    assert result.parents[0].text == result.children[0].text == text
    assert_contract(text, blocks, result, 32, 32, "o200k_base")


def test_code_fragments_keep_the_original_kind_and_heading_path():
    text = "# Guide\n\n```text\n" + "# Literal heading\n- Literal list\n" * 12 + "```\n"
    blocks, result = split(text, 24, 12)
    code_index = next(i for i, block in enumerate(blocks) if block.kind == "code")
    code_children = [c for c in result.children if code_index in c.source_block_indices]
    assert len({c.parent_id for c in code_children}) > 1
    assert all(c.source_block_indices == [code_index] for c in code_children)
    assert all(c.heading_path == ["Guide"] for c in code_children)
    assert_contract(text, blocks, result, 24, 12)


def test_ids_are_repeatable_file_specific_and_survive_serialization_without_mutating_blocks():
    text = "# Guide\n\n" + "A useful sentence. " * 20
    blocks = parse_markdown(text)
    before = [block.model_dump() for block in blocks]
    kwargs = dict(parent_max_tokens=24, child_max_tokens=8, encoding_name="cl100k_base")
    first = split_parent_child(text, blocks, "file-1", **kwargs)
    assert first == split_parent_child(text, blocks, "file-1", **kwargs)
    assert first == ParentChildChunks.model_validate_json(first.model_dump_json())
    assert [block.model_dump() for block in blocks] == before
    other = split_parent_child(text, blocks, "file-2", **kwargs)
    assert {p.parent_id for p in first.parents}.isdisjoint(p.parent_id for p in other.parents)
    assert {c.chunk_id for c in first.children}.isdisjoint(c.chunk_id for c in other.children)
    assert_contract(text, blocks, first, 24, 8)


@pytest.mark.parametrize("parent_budget,child_budget", [(64, 16), (256, 64)])
def test_frozen_markdown_corpus_preserves_source_and_unique_parent_containment(parent_budget, child_budget):
    corpus = Path(__file__).resolve().parents[1] / "evals/materials/deepseek/md"
    paths = sorted(corpus.rglob("*.md"))
    assert paths
    for path in paths:
        text = path.read_bytes().decode("utf-8")
        blocks, result = split(text, parent_budget, child_budget)
        assert_contract(text, blocks, result, parent_budget, child_budget)
