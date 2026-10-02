"""Deletion workflows with real SQLite and Chroma, and offline model doubles."""

from unittest.mock import Mock

import pytest

from knowledgebase.providers.llm import LLMClient
from knowledgebase.rag.document_chunker import DocumentChunker
from knowledgebase.rag.generation import INSUFFICIENT_EVIDENCE
from knowledgebase.rag.retrieval import Retriever
from knowledgebase.services.files import FileService
from knowledgebase.rag.client import RagClient
from knowledgebase.storage.operations import (
    create_file,
    get_chunks,
    get_file,
    get_files,
    update_file_status,
)


def test_delete_removes_only_target_and_new_answers_use_remaining_file(storage, embeddings):
    sessions, store, collection = storage
    removed = FileService(
        sessions,
        store,
        embeddings=embeddings,
        chunker=DocumentChunker(chunk_size=7, overlap=0, chunking_strategy="character"),
    ).ingest("notes.txt", b"First. Second.")
    kept = FileService(sessions, store, embeddings=embeddings).ingest(
        "notes.txt", b"Keep this source."
    )

    assert FileService(sessions, store).delete(removed) is None

    with sessions() as session:
        assert get_file(session, removed) is None
        assert get_chunks(session, removed) == []
        assert get_file(session, kept).status == "ready"
        assert get_chunks(session, kept)[0].text == "Keep this source."
    assert collection.get()["ids"] == [f"{kept}:child:0"]
    llm = Mock(spec=LLMClient)
    llm.generate.return_value = "Keep this source. [1]"
    answer = RagClient(sessions, Retriever(embeddings, store), llm).answer("What remains?")
    assert [source.file_id for source in answer.sources] == [kept]
    prompt = llm.generate.call_args.args[0][0]["content"]
    assert "Keep this source." in prompt
    assert "First." not in prompt and "Second." not in prompt


def test_ingest_ask_delete_ask_returns_insufficient_evidence(storage, embeddings):
    sessions, store, collection = storage
    file_id = FileService(sessions, store, embeddings=embeddings).ingest(
        "hours.txt", b"The library closes at 5 PM."
    )
    llm = Mock(spec=LLMClient)
    llm.generate.return_value = "The library closes at 5 PM. [1]"
    before = RagClient(sessions, Retriever(embeddings, store), llm).answer(
        "When does the library close?"
    )
    assert before.sources[0].file_id == file_id
    assert before.answer == llm.generate.return_value

    FileService(sessions, store).delete(file_id)
    embeddings.reset_mock()
    llm.reset_mock()
    after = RagClient(sessions, Retriever(embeddings, store), llm).answer(
        "When does the library close?"
    )
    assert after.answer == INSUFFICIENT_EVIDENCE
    assert after.sources == []
    embeddings.embed_query.assert_not_called()
    llm.generate.assert_not_called()
    assert collection.count() == 0


@pytest.mark.parametrize("partial_delete", [False, True])
def test_vector_failure_leaves_committed_nonready_file_and_cleanup_is_retryable(
    storage, embeddings, partial_delete
):
    sessions, store, collection = storage
    removed = FileService(
        sessions,
        store,
        embeddings=embeddings,
        chunker=DocumentChunker(chunk_size=7, overlap=0, chunking_strategy="character"),
    ).ingest("notes.txt", b"First. Second.")
    kept = FileService(sessions, store, embeddings=embeddings).ingest("keep.txt", b"Keep.")
    failure = RuntimeError("Vector deletion failed.")

    def fail_delete(file_id):
        # A new session must see exclusion before any vector removal begins.
        with sessions() as session:
            assert get_file(session, file_id).status == "failed"
            hits = Retriever(embeddings, store, top_k=5).retrieve("What remains?", session).chunks
            assert [hit.chunk.file_id for hit in hits] == [kept]
        if partial_delete:
            collection.delete(ids=[f"{file_id}:0"])
        raise failure

    failing_store = Mock(wraps=store)
    failing_store.delete_by_file_id.side_effect = fail_delete
    with pytest.raises(RuntimeError) as caught:
        FileService(sessions, failing_store).delete(removed)
    assert caught.value is failure
    with sessions() as session:
        file = get_file(session, removed)
        assert file.status == "failed"
        assert "Retry deletion" in file.error_message
        assert len(get_chunks(session, removed)) == 2
        assert [
            hit.chunk.file_id
            for hit in Retriever(embeddings, store).retrieve("What remains?", session).chunks
        ] == [kept]
    assert len(collection.get(where={"file_id": removed})["ids"]) == (1 if partial_delete else 2)

    FileService(sessions, store).delete(removed)
    with sessions() as session:
        assert get_file(session, removed) is None
        assert get_chunks(session, removed) == []
        assert get_file(session, kept).status == "ready"
    assert collection.get()["ids"] == [f"{kept}:child:0"]


def test_sql_cleanup_failure_rolls_back_chunks_and_can_retry_without_vectors(
    storage, embeddings, monkeypatch
):
    from knowledgebase.services import files

    sessions, store, collection = storage
    file_id = FileService(sessions, store, embeddings=embeddings).ingest("notes.txt", b"Notes.")
    failure = RuntimeError("File record deletion failed.")
    original = files.delete_file_record
    monkeypatch.setattr(files, "delete_file_record", Mock(side_effect=failure))

    with pytest.raises(RuntimeError) as caught:
        FileService(sessions, store).delete(file_id)
    assert caught.value is failure
    assert collection.count() == 0
    with sessions() as session:
        assert get_file(session, file_id).status == "failed"
        assert len(get_chunks(session, file_id)) == 1
        assert Retriever(embeddings, store).retrieve("What is in the notes?", session).chunks == []

    monkeypatch.setattr(files, "delete_file_record", original)
    FileService(sessions, store).delete(file_id)
    with sessions() as session:
        assert get_files(session) == []
        assert get_chunks(session, file_id) == []


def test_failed_ingestion_record_without_chunks_or_vectors_can_be_deleted(storage):
    sessions, store, collection = storage
    with sessions.begin() as session:
        create_file(session, "failed-file", "notes.txt")
        update_file_status(session, "failed-file", "failed", "Embedding failed.")
    FileService(sessions, store).delete("failed-file")
    with sessions() as session:
        assert get_files(session) == []
    assert collection.count() == 0


def test_missing_file_raises_before_vector_cleanup(storage):
    sessions, store, collection = storage
    observed_store = Mock(wraps=store)
    with pytest.raises(LookupError, match="missing"):
        FileService(sessions, observed_store).delete("missing")
    observed_store.delete_by_file_id.assert_not_called()
    with sessions() as session:
        assert get_files(session) == []
