from unittest.mock import Mock

import pytest

from knowledgebase.rag.chunking import split_text
from knowledgebase.rag.retrieval import retrieve
from knowledgebase.services.files import InvalidUploadError, ingest_file
from knowledgebase.storage.operations import get_chunks, get_file, get_files


def test_ingested_file_is_ready_and_retrievable(storage, embeddings):
    sessions, store, collection = storage
    text = "A library stores books."

    file_id = ingest_file("Library.TXT", text.encode("utf-8"), sessions, embeddings, store)

    with sessions() as session:
        file = get_file(session, file_id)
        assert file.file_name == "Library.TXT"
        assert file.status == "ready"
        assert file.error_message is None
        results = retrieve("Where are books stored?", session, embeddings, store, top_k=1)

    assert results[0].chunk.file_id == file_id
    assert results[0].chunk.text == text
    assert results[0].distance == pytest.approx(0.0)
    assert collection.count() == 1


def test_ingestion_preserves_text_offsets_and_uses_chunk_settings(storage, embeddings):
    sessions, store, collection = storage
    text = "  café 🙂\r\nSecond line.\n"

    file_id = ingest_file(
        "notes.txt", text.encode("utf-8"), sessions, embeddings, store,
        chunk_size=8, overlap=2,
    )

    expected = split_text(text, file_id, chunk_size=8, overlap=2)
    with sessions() as session:
        assert get_chunks(session, file_id) == expected
    embeddings.embed_documents.assert_called_once_with([chunk.text for chunk in expected])
    assert collection.count() == len(expected)


def test_same_filename_gets_distinct_file_ids(storage, embeddings):
    sessions, store, collection = storage

    first = ingest_file("notes.txt", b"First.", sessions, embeddings, store)
    second = ingest_file("notes.txt", b"Second.", sessions, embeddings, store)

    assert first != second
    with sessions() as session:
        assert get_chunks(session, first)[0].text == "First."
        assert get_chunks(session, second)[0].text == "Second."
    assert collection.count() == 2


@pytest.mark.parametrize(
    ("name", "content", "error_type"),
    [
        ("notes.pdf", b"Text.", InvalidUploadError),
        ("notes.txt", b"\xff", InvalidUploadError),
        ("notes.txt", b"", InvalidUploadError),
        ("notes.txt", b" \r\n\t", InvalidUploadError),
    ],
)
def test_invalid_upload_is_rejected_before_creating_records(
    storage, embeddings, name, content, error_type
):
    sessions, store, collection = storage

    with pytest.raises(error_type):
        ingest_file(name, content, sessions, embeddings, store)

    with sessions() as session:
        assert get_files(session) == []
    embeddings.embed_documents.assert_not_called()
    assert collection.count() == 0


def test_processing_is_visible_until_all_writes_finish(storage, embeddings):
    sessions, store, collection = storage

    def embed(texts):
        with sessions() as session:
            assert get_files(session)[0].status == "processing"
        return [[1.0, 0.0] for text in texts]

    def upsert(chunks, vectors):
        store.upsert_chunks(chunks, vectors)
        with sessions() as session:
            assert get_file(session, chunks[0].file_id).status == "processing"

    embeddings.embed_documents.side_effect = embed
    observed_store = Mock(wraps=store)
    observed_store.upsert_chunks.side_effect = upsert

    file_id = ingest_file("notes.txt", b"Text.", sessions, embeddings, observed_store)

    with sessions() as session:
        assert get_file(session, file_id).status == "ready"
    assert collection.count() == 1


def test_embedding_failure_is_recorded_and_propagated(storage, embeddings):
    sessions, store, collection = storage
    failure = RuntimeError("Embedding request failed.")
    embeddings.embed_documents.side_effect = failure

    with pytest.raises(RuntimeError) as caught:
        ingest_file("notes.txt", b"Text.", sessions, embeddings, store)

    assert caught.value is failure
    with sessions() as session:
        file = get_files(session)[0]
        assert file.status == "failed"
        assert file.error_message == str(failure)
        assert get_chunks(session, file.file_id) == []
    assert collection.count() == 0


def test_partial_vector_failure_rolls_back_chunks_and_cleans_only_new_file(
    storage, embeddings
):
    sessions, store, collection = storage
    existing_id = ingest_file("existing.txt", b"Keep.", sessions, embeddings, store)
    failure = RuntimeError("Vector write failed.")

    def partial_upsert(chunks, vectors):
        store.upsert_chunks(chunks[:1], vectors[:1])
        raise failure

    failing_store = Mock(wraps=store)
    failing_store.upsert_chunks.side_effect = partial_upsert
    with pytest.raises(RuntimeError) as caught:
        ingest_file(
            "new.txt", b"First. Second.", sessions, embeddings, failing_store,
            chunk_size=7, overlap=0,
        )

    assert caught.value is failure
    with sessions() as session:
        failed = next(file for file in get_files(session) if file.file_id != existing_id)
        assert failed.status == "failed"
        assert failed.error_message == str(failure)
        assert get_chunks(session, failed.file_id) == []
        assert get_file(session, existing_id).status == "ready"
    assert collection.get()["ids"] == [f"{existing_id}:0"]


def test_ready_update_failure_rolls_back_chunks_and_removes_written_vectors(
    storage, embeddings, monkeypatch
):
    from knowledgebase.services import files

    sessions, store, collection = storage
    update_status = files.update_file_status
    failure = RuntimeError("Ready update failed.")

    def fail_ready(session, file_id, status, error_message=None):
        if status == "ready":
            raise failure
        update_status(session, file_id, status, error_message)

    monkeypatch.setattr(files, "update_file_status", fail_ready)
    with pytest.raises(RuntimeError) as caught:
        ingest_file("notes.txt", b"Text.", sessions, embeddings, store)

    assert caught.value is failure
    with sessions() as session:
        file = get_files(session)[0]
        assert file.status == "failed"
        assert get_chunks(session, file.file_id) == []
    assert collection.count() == 0
