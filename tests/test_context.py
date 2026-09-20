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
        "[1]\n  café\ncloses at 5 PM.\n\n\n[2]\nLibrary hours."
    )
