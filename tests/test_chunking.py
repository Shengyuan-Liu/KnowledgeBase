import pytest

from knowledgebase.rag.chunking import split_text
from knowledgebase.schemas import Chunk


@pytest.mark.parametrize(
    ("text", "chunk_size", "overlap", "expected"),
    [
        ("", 6, 2, []),
        ("abc", 6, 2, [("abc", 0, 3)]),
        ("abcdef", 6, 2, [("abcdef", 0, 6)]),
        ("abcdefghij", 6, 2, [("abcdef", 0, 6), ("efghij", 4, 10)]),
        ("abcdefghi", 6, 2, [("abcdef", 0, 6), ("efghi", 4, 9)]),
        ("abcdefghij", 6, 0, [("abcdef", 0, 6), ("ghij", 6, 10)]),
        ("abcdef", 3, 0, [("abc", 0, 3), ("def", 3, 6)]),
        ("abcd", 3, 2, [("abc", 0, 3), ("bcd", 1, 4)]),
        ("ab", 1, 0, [("a", 0, 1), ("b", 1, 2)]),
        ("  a\n\tb  ", 5, 1, [("  a\n\t", 0, 5), ("\tb  ", 4, 8)]),
        (" \n\t ", 6, 2, [(" \n\t ", 0, 4)]),
        ("aé🙂bc", 3, 1, [("aé🙂", 0, 3), ("🙂bc", 2, 5)]),
    ],
    ids=[
        "empty", "short", "exact-size", "overlap", "short-tail",
        "no-overlap", "exact-multiple", "maximum-overlap", "single-character",
        "preserve-whitespace", "whitespace-only", "unicode-offsets",
    ],
)
def test_split_text_preserves_text_and_metadata(text, chunk_size, overlap, expected):
    chunks = split_text(text, "file-1", chunk_size, overlap)

    assert len(chunks) == len(expected)
    for index, (chunk, (excerpt, start, end)) in enumerate(zip(chunks, expected)):
        assert isinstance(chunk, Chunk)
        assert chunk.file_id == "file-1"
        assert chunk.index == index
        assert chunk.chunk_id
        assert (chunk.text, chunk.start_offset, chunk.end_offset) == (excerpt, start, end)
        assert chunk.text == text[chunk.start_offset:chunk.end_offset]
    assert len({chunk.chunk_id for chunk in chunks}) == len(chunks)


@pytest.mark.parametrize("text", ["", "abcdefghij"], ids=["empty", "nonempty"])
@pytest.mark.parametrize(
    ("chunk_size", "overlap", "message"),
    [(0, 0, "chunk_size"), (-1, 0, "chunk_size"),
     (6, -1, "overlap"), (6, 6, "overlap"), (6, 7, "overlap")],
)
def test_split_text_rejects_invalid_parameters(text, chunk_size, overlap, message):
    with pytest.raises(ValueError, match=message):
        split_text(text, "file-1", chunk_size, overlap)


def test_chunk_ids_are_repeatable_and_distinct_between_files():
    first = split_text("abcdefghij", "file-1", 6, 2)
    repeated = split_text("abcdefghij", "file-1", 6, 2)
    other_file = split_text("abcdefghij", "file-2", 6, 2)

    assert first == repeated
    assert {chunk.chunk_id for chunk in first}.isdisjoint(
        chunk.chunk_id for chunk in other_file
    )


def test_default_settings_cover_the_document_with_overlap():
    text = "a" * 300

    chunks = split_text(text, "file-1")

    assert [(chunk.start_offset, chunk.end_offset) for chunk in chunks] == [
        (0, 256), (192, 300)
    ]
    assert all(chunk.text == text[chunk.start_offset:chunk.end_offset] for chunk in chunks)
