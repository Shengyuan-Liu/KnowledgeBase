from pathlib import Path

import pytest

from knowledgebase.rag.parsing import parse_markdown, parse_txt


def assert_source_spans(text, blocks):
    """Every nonblank source character is retained once, in source order."""
    previous_end = 0
    for block in blocks:
        assert previous_end <= block.start_offset < block.end_offset <= len(text)
        assert not text[previous_end:block.start_offset].strip()
        assert block.text == text[block.start_offset:block.end_offset]
        previous_end = block.end_offset
    assert not text[previous_end:].strip()


@pytest.mark.parametrize("parse", [parse_txt, parse_markdown])
@pytest.mark.parametrize("text", ["", " \t\r\n\n", "One paragraph", "One paragraph\n"])
def test_empty_and_single_paragraph_sources(parse, text):
    blocks = parse(text)

    assert_source_spans(text, blocks)
    assert len(blocks) == (1 if text.strip() else 0)
    if blocks:
        assert blocks[0].kind == "paragraph"
        assert blocks[0].heading_path == []


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_txt_preserves_paragraphs_and_does_not_interpret_markdown(newline):
    first = f"  # Notes{newline}- café 🙂{newline}continued{newline}"
    second = "```python"
    text = newline + first + f" \t{newline}" + second

    blocks = parse_txt(text)

    assert_source_spans(text, blocks)
    assert [block.text for block in blocks] == [first, second]
    assert all(block.kind == "paragraph" and block.heading_path == [] for block in blocks)


def test_heading_paths_follow_levels_and_reset_for_siblings():
    text = (
        "Introduction.\n\n# Guide\n\nOverview.\n\n"
        "### Install\n\nInstall steps.\n\n## Usage\n\nUse it.\n\n"
        "# Reference\n\nFields."
    )

    blocks = parse_markdown(text)

    assert_source_spans(text, blocks)
    assert [block.heading_path for block in blocks] == [
        [], ["Guide"], ["Guide"], ["Guide", "Install"], ["Guide", "Install"],
        ["Guide", "Usage"], ["Guide", "Usage"], ["Reference"], ["Reference"],
    ]
    assert [block.heading_level for block in blocks if block.kind == "heading"] == [1, 3, 2, 1]
    assert all(block.heading_level is None for block in blocks if block.kind != "heading")


def test_setext_and_atx_headings_keep_inline_markdown_as_metadata():
    text = "**Guide**\n=========\n\nAPI `fields`\n------------\n\n### Next ###\n"

    blocks = parse_markdown(text)

    assert_source_spans(text, blocks)
    assert [block.heading_path for block in blocks] == [
        ["**Guide**"], ["**Guide**", "API `fields`"],
        ["**Guide**", "API `fields`", "Next"],
    ]


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_markdown_offsets_preserve_original_newlines_and_unicode(newline):
    text = newline.join(["# Café 🙂", "", "Résumé\u2028still one line.", "", "End."])

    blocks = parse_markdown(text)

    assert_source_spans(text, blocks)
    assert [block.text for block in blocks] == [
        f"# Café 🙂{newline}", f"Résumé\u2028still one line.{newline}", "End.",
    ]
    assert blocks[-1].start_offset == text.index("End.")


@pytest.mark.parametrize("fence", ["```", "~~~~"])
def test_fenced_code_is_one_block_and_does_not_change_heading_path(fence):
    code = f"{fence}python\n# Not a heading\n\n- Not a list\n{fence}\n"
    text = f"# Guide\n\n{code}\nAfter.\n"

    blocks = parse_markdown(text)

    assert_source_spans(text, blocks)
    assert [block.kind for block in blocks] == ["heading", "code", "paragraph"]
    assert blocks[1].text == code
    assert all(block.heading_path == ["Guide"] for block in blocks)


def test_unclosed_fence_preserves_content_to_end_of_source():
    text = "# Guide\n\n```python\nprint('hello')\n# Still code"

    blocks = parse_markdown(text)

    assert_source_spans(text, blocks)
    assert [block.kind for block in blocks] == ["heading", "code"]
    assert blocks[-1].text == "```python\nprint('hello')\n# Still code"


def test_lists_tables_and_quotes_remain_nonoverlapping_containers():
    unordered = "- First\n  - Nested\n\n- Second\n"
    ordered = "1. Install\n2. Run\n"
    table = "| Field | Value |\n| --- | ---: |\n| name | `a\\|b` |\n"
    quote = "> ## Quoted heading\n>\n> Quoted paragraph.\n"
    text = f"# Guide\n\n{unordered}\n{ordered}\n{table}\n{quote}\nAfter."

    blocks = parse_markdown(text)

    assert_source_spans(text, blocks)
    assert [block.kind for block in blocks] == [
        "heading", "list", "list", "table", "blockquote", "paragraph",
    ]
    assert [block.text.rstrip("\n") for block in blocks[1:5]] == [
        value.rstrip("\n") for value in [unordered, ordered, table, quote]
    ]
    assert all(block.heading_path == ["Guide"] for block in blocks)


def test_indented_code_thematic_break_and_link_definitions_are_retained():
    text = (
        "# Guide\n\n    print('hello')\n\n---\n\n"
        "See [docs][api].\n\n[api]: https://example.com/docs \"API\"\n"
        "[api]: https://example.com/duplicate\n"
    )

    blocks = parse_markdown(text)

    assert_source_spans(text, blocks)
    assert [block.kind for block in blocks] == [
        "heading", "code", "thematic_break", "paragraph", "reference", "reference",
    ]


def test_html_links_and_images_are_preserved_as_source_text():
    text = (
        '<script>alert("example")</script>\n\n'
        "[remote](https://example.com/page) ![image](https://example.com/image.png)"
    )

    blocks = parse_markdown(text)

    assert_source_spans(text, blocks)
    assert [block.kind for block in blocks] == ["paragraph", "paragraph"]
    assert blocks[0].text == '<script>alert("example")</script>\n'


def test_heading_state_does_not_leak_between_documents():
    parse_markdown("# First\n\nContent.")

    blocks = parse_markdown("Unrelated content.")

    assert blocks[0].heading_path == []


def test_frozen_deepseek_corpus_retains_all_nonblank_source_text():
    corpus = Path(__file__).resolve().parents[1] / "evals/materials/deepseek/md"
    paths = sorted(corpus.rglob("*.md"))
    assert paths
    for path in paths:
        text = path.read_bytes().decode("utf-8")
        assert_source_spans(text, parse_markdown(text))
