from unittest.mock import Mock

import chromadb
import pytest

from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient
from knowledgebase.rag.generation import INSUFFICIENT_EVIDENCE
from knowledgebase.schemas import ChatAnswer
from knowledgebase.services.chat import answer_question
from knowledgebase.services.files import ingest_file
from knowledgebase.storage.database import build_engine, build_session_factory, init_db
from knowledgebase.storage.vectordb import ChromaStore


@pytest.fixture
def storage(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'chat.db'}")
    init_db(engine)
    client = chromadb.PersistentClient(path=str(tmp_path / "chroma"))
    collection = client.create_collection(
        name="chat-chunks",
        embedding_function=None,
        configuration={"hnsw": {"space": "cosine"}},
    )
    try:
        yield build_session_factory(engine), ChromaStore(collection)
    finally:
        engine.dispose()


@pytest.mark.parametrize("top_k", [2, 3])
def test_ingestion_to_answer_keeps_sources_aligned_with_prompt(storage, top_k):
    sessions, store = storage
    embeddings = Mock(spec=EmbeddingClient)
    embeddings.embed_documents.side_effect = [
        [[0.6, 0.8], [0.8, 0.6]],
        [[1.0, 0.0]],
    ]
    embeddings.embed_query.return_value = [1.0, 0.0]
    first_id = ingest_file(
        "notes.txt", b"First. Second.", sessions, embeddings, store,
        chunk_size=7, overlap=0,
    )
    second_text = "  The café closes at 5 PM.\n"
    second_id = ingest_file(
        "hours.txt", second_text.encode("utf-8"), sessions, embeddings, store
    )
    llm = Mock(spec=LLMClient)
    llm.generate.return_value = "The café closes at 5 PM. [1]\n"
    question = "  When does the café close?\n"

    result = answer_question(question, sessions, embeddings, store, llm, top_k=top_k)

    assert isinstance(result, ChatAnswer)
    assert result.answer == "The café closes at 5 PM. [1]\n"
    assert [source.source_id for source in result.sources] == list(range(1, top_k + 1))
    assert [source.file_id for source in result.sources] == [
        second_id, first_id, first_id
    ][:top_k]
    assert [source.file_name for source in result.sources] == [
        "hours.txt", "notes.txt", "notes.txt"
    ][:top_k]
    assert [source.chunk_id for source in result.sources] == [
        f"{second_id}:0", f"{first_id}:1", f"{first_id}:0"
    ][:top_k]
    assert [source.text for source in result.sources] == [
        second_text, "Second.", "First. "
    ][:top_k]
    assert [source.distance for source in result.sources] == pytest.approx(
        [0.0, 0.2, 0.4][:top_k]
    )
    embeddings.embed_query.assert_called_once_with(question)
    llm.generate.assert_called_once()
    user_message = llm.generate.call_args.args[0][1]
    expected_context = "[1]\n  The café closes at 5 PM.\n\n\n[2]\nSecond."
    if top_k == 3:
        expected_context += "\n\n[3]\nFirst. "
    assert user_message == {
        "role": "user",
        "content": f"Question:\n{question}\n\nSources:\n{expected_context}",
    }


def test_empty_knowledge_base_returns_no_sources_without_model_calls(storage):
    sessions, store = storage
    embeddings = Mock(spec=EmbeddingClient)
    llm = Mock(spec=LLMClient)

    result = answer_question("When does the café close?", sessions, embeddings, store, llm)

    assert result == ChatAnswer(answer=INSUFFICIENT_EVIDENCE, sources=[])
    embeddings.embed_query.assert_not_called()
    llm.generate.assert_not_called()
