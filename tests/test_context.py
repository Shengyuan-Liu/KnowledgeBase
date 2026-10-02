from knowledgebase.rag.context import build_context
from knowledgebase.schemas import Chunk, RetrievedChunk


def test_context_preserves_retrieval_order_and_source_text():
    chunks = [
        RetrievedChunk(
            file_name="notes.txt",
            chunk=Chunk(
                chunk_id=f"chunk-{index}",
                file_id="file-1",
                text=text,
                index=index,
                start_offset=start,
                end_offset=start + len(text),
            ),
            distance=distance,
        )
        for index, text, start, distance in [
            (2, "  café\ncloses at 5 PM.\n", 80, 0.1),
            (0, "Library hours.", 0, 0.2),
        ]
    ]

    assert build_context(chunks) == (
        '[1]\nSource metadata: {"file_name": "notes.txt", "heading_path": []}\nExcerpt:\n'
        '  café\ncloses at 5 PM.\n\n\n'
        '[2]\nSource metadata: {"file_name": "notes.txt", "heading_path": []}\nExcerpt:\nLibrary hours.'
    )


def test_nested_heading_identity_is_separate_from_exact_unicode_excerpt():
    from knowledgebase.schemas import Chunk

    text = '```python\r\nprint("café")\r\n```\r\n'
    chunk = Chunk(chunk_id='child', file_id='guide', text=text, index=0,
                            start_offset=15, end_offset=15 + len(text),
                            heading_path=['API', 'Examples > Python'], source_block_indices=[2],
                            token_count=12, tokenizer='cl100k_base', max_tokens=512)
    item = RetrievedChunk(chunk=chunk, file_name='guide.md', distance=0.1)
    result = build_context([item])
    assert result == ('[1]\nSource metadata: {"file_name": "guide.md", '
                      '"heading_path": ["API", "Examples > Python"]}\nExcerpt:\n' + text)
    assert chunk.text == text and chunk.start_offset == 15
    assert build_context([]) == ''
