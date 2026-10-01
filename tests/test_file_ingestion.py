from unittest.mock import Mock

import pytest
from sqlalchemy import select

from knowledgebase.rag.chunking import DocumentChunker, split_text
from knowledgebase.rag.retrieval import Retriever
from knowledgebase.services.files import FileService, InvalidUploadError
from knowledgebase.storage.models import ChunkStructureRecord, DocumentSourceRecord
from knowledgebase.storage.operations import (
    get_chunks,
    get_document_source,
    get_file,
    get_files,
)


def test_ingested_file_is_ready_and_retrievable(storage, embeddings):
    sessions, store, collection = storage
    text = "A library stores books."

    file_id = FileService(sessions, store, embeddings=embeddings).ingest(
        "Library.TXT", text.encode("utf-8")
    )

    with sessions() as session:
        file = get_file(session, file_id)
        assert file.file_name == "Library.TXT"
        assert file.status == "ready"
        assert file.error_message is None
        results = (
            Retriever(embeddings, store, top_k=1)
            .retrieve("Where are books stored?", session)
            .chunks
        )

    assert results[0].chunk.file_id == file_id
    assert results[0].chunk.text == text
    assert results[0].distance == pytest.approx(0.0)
    assert collection.count() == 1


@pytest.mark.parametrize("name", ["notes.txt", "Guide.MD"])
def test_structural_upload_persists_source_blocks_and_indexed_chunks(storage, embeddings, name):
    sessions, store, collection = storage
    text = "# Guide\r\n\r\nThe café closes at 5 PM.\r\n\r\n## Setup\r\n\r\nInstall the package.\r\n"
    file_id = FileService(
        sessions,
        store,
        embeddings=embeddings,
        chunker=DocumentChunker(
            chunking_strategy="structural", chunk_max_tokens=16, chunk_tokenizer="cl100k_base"
        ),
    ).ingest(name, text.encode("utf-8"))

    with sessions() as session:
        source = get_document_source(session, file_id)
        chunks = get_chunks(session, file_id)
        assert get_file(session, file_id).status == "ready"
        assert source.text == text
        assert source.type == ("md" if name.endswith("MD") else "txt")
        assert all(chunk.type == "flat" and chunk.token_count is not None for chunk in chunks)
        assert all(chunk.token_count <= 16 and chunk.max_tokens == 16 for chunk in chunks)
        assert all(chunk.text == text[chunk.start_offset : chunk.end_offset] for chunk in chunks)
        if source.type == "md":
            assert {tuple(chunk.heading_path) for chunk in chunks} == {
                ("Guide",),
                ("Guide", "Setup"),
            }
        else:
            assert all(chunk.heading_path == [] for chunk in chunks)
        results = (
            Retriever(embeddings, store, top_k=len(chunks))
            .retrieve("What does the guide say?", session)
            .chunks
        )
        assert {hit.chunk.chunk_id for hit in results} == {chunk.chunk_id for chunk in chunks}
    embeddings.embed_documents.assert_called_once_with([chunk.text for chunk in chunks])
    assert collection.count() == len(chunks)


def test_parser_failure_leaves_a_failed_record_without_indexing(storage, embeddings, monkeypatch):
    from knowledgebase.rag import parsing

    sessions, store, collection = storage
    monkeypatch.setattr(parsing, "parse_markdown", Mock(side_effect=ValueError("Parsing failed.")))
    with pytest.raises(ValueError, match="Parsing failed"):
        FileService(sessions, store, embeddings=embeddings).ingest("guide.md", b"# Guide")
    with sessions() as session:
        file = get_files(session)[0]
        assert file.status == "failed"
        assert get_document_source(session, file.file_id) is None
        assert get_chunks(session, file.file_id) == []
    embeddings.embed_documents.assert_not_called()
    assert collection.count() == 0


def test_partial_structural_index_failure_rolls_back_source_and_metadata(storage, embeddings):
    sessions, store, collection = storage

    def partial_upsert(chunks, vectors):
        store.upsert_chunks(chunks[:1], vectors[:1])
        raise RuntimeError("Vector write failed.")

    broken = Mock(wraps=store)
    broken.upsert_chunks.side_effect = partial_upsert
    with pytest.raises(RuntimeError, match="Vector write failed"):
        FileService(sessions, broken, embeddings=embeddings).ingest(
            "guide.md", b"# First\n\nFirst.\n\n# Second\n\nSecond."
        )
    with sessions() as session:
        file = get_files(session)[0]
        assert file.status == "failed"
        assert get_document_source(session, file.file_id) is None
        assert get_chunks(session, file.file_id) == []
        assert session.scalars(select(ChunkStructureRecord)).all() == []
        assert session.scalars(select(DocumentSourceRecord)).all() == []
    assert collection.count() == 0


def test_ingestion_preserves_text_offsets_and_uses_chunk_settings(storage, embeddings):
    sessions, store, collection = storage
    text = "  café 🙂\r\nSecond line.\n"

    file_id = FileService(
        sessions,
        store,
        embeddings=embeddings,
        chunker=DocumentChunker(chunk_size=8, overlap=2, chunking_strategy="character"),
    ).ingest("notes.txt", text.encode("utf-8"))

    expected = split_text(text, file_id, chunk_size=8, overlap=2)
    with sessions() as session:
        assert get_chunks(session, file_id) == expected
    embeddings.embed_documents.assert_called_once_with([chunk.text for chunk in expected])
    assert collection.count() == len(expected)


def test_same_filename_gets_distinct_file_ids(storage, embeddings):
    sessions, store, collection = storage

    first = FileService(sessions, store, embeddings=embeddings).ingest("notes.txt", b"First.")
    second = FileService(sessions, store, embeddings=embeddings).ingest("notes.txt", b"Second.")

    assert first != second
    with sessions() as session:
        assert get_chunks(session, first)[0].text == "First."
        assert get_chunks(session, second)[0].text == "Second."
    assert collection.count() == 2


@pytest.mark.parametrize(
    ("name", "content", "error_type"),
    [
        ("notes.docx", b"Text.", InvalidUploadError),
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
        FileService(sessions, store, embeddings=embeddings).ingest(name, content)

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

    file_id = FileService(sessions, observed_store, embeddings=embeddings).ingest(
        "notes.txt", b"Text."
    )

    with sessions() as session:
        assert get_file(session, file_id).status == "ready"
    assert collection.count() == 1


def test_embedding_failure_is_recorded_and_propagated(storage, embeddings):
    sessions, store, collection = storage
    failure = RuntimeError("Embedding request failed.")
    embeddings.embed_documents.side_effect = failure

    with pytest.raises(RuntimeError) as caught:
        FileService(sessions, store, embeddings=embeddings).ingest("notes.txt", b"Text.")

    assert caught.value is failure
    with sessions() as session:
        file = get_files(session)[0]
        assert file.status == "failed"
        assert file.error_message == str(failure)
        assert get_chunks(session, file.file_id) == []
    assert collection.count() == 0


def test_partial_vector_failure_rolls_back_chunks_and_cleans_only_new_file(storage, embeddings):
    sessions, store, collection = storage
    existing_id = FileService(sessions, store, embeddings=embeddings).ingest(
        "existing.txt", b"Keep."
    )
    failure = RuntimeError("Vector write failed.")

    def partial_upsert(chunks, vectors):
        store.upsert_chunks(chunks[:1], vectors[:1])
        raise failure

    failing_store = Mock(wraps=store)
    failing_store.upsert_chunks.side_effect = partial_upsert
    with pytest.raises(RuntimeError) as caught:
        FileService(
            sessions,
            failing_store,
            embeddings=embeddings,
            chunker=DocumentChunker(chunk_size=7, overlap=0, chunking_strategy="character"),
        ).ingest("new.txt", b"First. Second.")

    assert caught.value is failure
    with sessions() as session:
        failed = next(file for file in get_files(session) if file.file_id != existing_id)
        assert failed.status == "failed"
        assert failed.error_message == str(failure)
        assert get_chunks(session, failed.file_id) == []
        assert get_file(session, existing_id).status == "ready"
    assert collection.get()["ids"] == [f"{existing_id}:child:0"]


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
        FileService(sessions, store, embeddings=embeddings).ingest("notes.txt", b"Text.")

    assert caught.value is failure
    with sessions() as session:
        file = get_files(session)[0]
        assert file.status == "failed"
        assert get_chunks(session, file.file_id) == []
    assert collection.count() == 0
