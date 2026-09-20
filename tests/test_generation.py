from unittest.mock import Mock

from knowledgebase.providers.llm import LLMClient
from knowledgebase.rag.generation import generate_answer
from knowledgebase.schemas import Chunk, RetrievedChunk


def test_empty_retrieval_returns_insufficient_evidence_without_calling_model():
    llm = Mock(spec=LLMClient)

    answer = generate_answer("When does the library close?", [], llm)

    assert answer == (
        "There is not enough information in the provided sources to answer this question."
    )
    llm.generate.assert_not_called()


def test_numbers_sources_in_retrieval_order_and_preserves_question_and_text():
    chunks = [
        RetrievedChunk(
            file_name="notes.txt",
            chunk=Chunk(
                chunk_id="chunk-z",
                file_id="file-b",
                text="  In fall 2026, the café closes at 5 PM.\n",
                index=3,
                start_offset=120,
                end_offset=163,
            ),
            distance=0.1,
        ),
        RetrievedChunk(
            file_name="notes.txt",
            chunk=Chunk(
                chunk_id="chunk-a",
                file_id="file-a",
                text="In spring 2026, the café closes at 4 PM.",
                index=0,
                start_offset=0,
                end_offset=38,
            ),
            distance=0.2,
        ),
    ]
    llm = Mock(spec=LLMClient)
    llm.generate.return_value = "It closes at 5 PM in fall 2026. [1]\n"

    answer = generate_answer("  When does the café close in fall 2026?\n", chunks, llm)

    assert answer == "It closes at 5 PM in fall 2026. [1]\n"
    llm.generate.assert_called_once()
    instructions, user_message = llm.generate.call_args.args[0]
    assert instructions["role"] == "developer"
    assert "using only the provided sources" in instructions["content"]
    assert "Cite supporting source numbers inline" in instructions["content"]
    assert "do not contain enough information" in instructions["content"]
    assert user_message == {
        "role": "user",
        "content": (
            "Question:\n  When does the café close in fall 2026?\n\n\nSources:\n"
            "[1]\n  In fall 2026, the café closes at 5 PM.\n\n\n"
            "[2]\nIn spring 2026, the café closes at 4 PM."
        ),
    }
