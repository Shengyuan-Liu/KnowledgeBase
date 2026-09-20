from unittest.mock import Mock

import pytest

from knowledgebase.rag.chunking import split_text
from knowledgebase.rag.retrieval import retrieve
from knowledgebase.storage.operations import (
    create_file,
    save_chunks,
    update_file_status,
)


@pytest.fixture
def retrieval_storage(storage):
    sessions, store, _ = storage
    with sessions.begin() as session:
        yield session, store


def index_file(session, store, file_id, text, vectors, status="ready"):
    create_file(session, file_id, f"{file_id}.txt")
    chunks = split_text(text, file_id, chunk_size=7, overlap=0)
    save_chunks(session, chunks)
    store.upsert_chunks(chunks, vectors)
    update_file_status(session, file_id, status)
    return chunks


def test_retrieve_returns_sqlite_text_offsets_and_distances_in_search_order(
    retrieval_storage, embeddings
):
    session, store = retrieval_storage
    chunks = index_file(
        session, store, "file-z", "  café\nSecond.", [[0.8, 0.6], [1.0, 0.0]]
    )
    other = index_file(session, store, "file-a", "Third.", [[0.0, 1.0]])

    result = retrieve("  A question?\n", session, embeddings, store, top_k=3)

    embeddings.embed_query.assert_called_once_with("  A question?\n")
    assert [item.chunk for item in result] == [chunks[1], chunks[0], other[0]]
    assert [item.file_name for item in result] == ["file-z.txt", "file-z.txt", "file-a.txt"]
    assert [item.distance for item in result] == pytest.approx([0.0, 0.2, 1.0])


def test_processing_and_failed_files_do_not_consume_top_k(retrieval_storage, embeddings):
    session, store = retrieval_storage
    for status in ["processing", "failed"]:
        index_file(session, store, status, "Hidden.", [[1.0, 0.0]], status=status)
    ready = index_file(
        session, store, "ready", "First. Second.", [[0.8, 0.6], [0.0, 1.0]]
    )

    result = retrieve("Question?", session, embeddings, store, top_k=2)

    assert [item.chunk for item in result] == ready
    assert [item.distance for item in result] == pytest.approx([0.2, 1.0])


@pytest.mark.parametrize("statuses", [[], ["processing", "failed"]])
def test_no_ready_files_returns_no_evidence_without_embedding(retrieval_storage, embeddings, statuses):
    session, store = retrieval_storage
    for status in statuses:
        index_file(session, store, status, "Hidden.", [[1.0, 0.0]], status=status)
    observed_store = Mock(wraps=store)

    assert retrieve("Question?", session, embeddings, observed_store) == []

    embeddings.embed_query.assert_not_called()
    observed_store.search.assert_not_called()


def test_no_vector_matches_returns_no_evidence(retrieval_storage, embeddings):
    session, store = retrieval_storage
    create_file(session, "ready", "ready.txt")
    update_file_status(session, "ready", "ready")

    assert retrieve("Question?", session, embeddings, store) == []
    embeddings.embed_query.assert_called_once_with("Question?")
