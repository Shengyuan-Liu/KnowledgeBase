from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from knowledgebase.rag.chunking import split_text
from knowledgebase.storage.models import FileRecord
from knowledgebase.schemas import Chunk, FileInfo
from knowledgebase.storage.operations import (
    create_file,
    delete_chunks,
    delete_file_record,
    get_file,
    get_files,
    get_chunks,
    get_chunks_by_ids,
    save_chunks,
    update_file_status,
)


def test_create_file_flushes_record_with_defaults(sessions):
    with sessions() as session:
        result = create_file(session, "file-1", "notes.txt")

        with session.no_autoflush:
            record = session.scalars(select(FileRecord)).one()
        assert result is None
        assert record.file_id == "file-1"
        assert record.file_name == "notes.txt"
        assert record.status == "processing"
        assert record.error_message is None
        assert isinstance(record.created_at, datetime)


def test_get_chunks_by_ids_loads_selected_chunks_across_files(sessions):
    first = split_text("First. Second.", "file-1", chunk_size=7, overlap=0)
    second = split_text("Third.", "file-2")
    with sessions.begin() as session:
        create_file(session, "file-1", "first.txt")
        create_file(session, "file-2", "second.txt")
        save_chunks(session, first + second)

    with sessions() as session:
        result = get_chunks_by_ids(session, [second[0].chunk_id, first[1].chunk_id])

    assert {chunk.chunk_id: chunk for chunk in result} == {
        second[0].chunk_id: second[0], first[1].chunk_id: first[1]
    }


def test_get_chunks_by_ids_with_no_ids_returns_no_chunks(sessions):
    with sessions.begin() as session:
        create_file(session, "file-1", "first.txt")
        save_chunks(session, split_text("First.", "file-1"))
        assert get_chunks_by_ids(session, []) == []


def test_create_file_persists_when_caller_commits(sessions):
    with sessions.begin() as session:
        create_file(session, "file-1", "notes.txt")

    with sessions() as reader:
        assert reader.get(FileRecord, "file-1").file_name == "notes.txt"


def test_create_file_can_be_rolled_back_by_caller(sessions):
    with sessions() as session:
        create_file(session, "file-1", "notes.txt")
        session.rollback()

    with sessions() as reader:
        assert reader.get(FileRecord, "file-1") is None


def test_create_file_rejects_duplicate_id_during_call(sessions):
    with sessions.begin() as session:
        create_file(session, "file-1", "original.txt")

    with sessions() as session:
        with pytest.raises(IntegrityError):
            create_file(session, "file-1", "replacement.txt")
        session.rollback()
        assert session.get(FileRecord, "file-1").file_name == "original.txt"


def test_get_files_returns_empty_list(sessions):
    with sessions() as session:
        assert get_files(session) == []


def test_get_files_returns_all_statuses_in_stable_newest_first_order(sessions):
    older = datetime(2026, 1, 1)
    newer = datetime(2026, 1, 2)
    with sessions.begin() as session:
        session.add_all([
            FileRecord(file_id="file-c", file_name="failed.txt", status="failed",
                       error_message="Embedding failed.", created_at=newer),
            FileRecord(file_id="file-a", file_name="ready.txt", status="ready",
                       created_at=older),
            FileRecord(file_id="file-b", file_name="pending.txt", status="processing",
                       created_at=newer),
        ])

    with sessions() as session:
        files = get_files(session)

    assert all(isinstance(file, FileInfo) for file in files)
    assert [file.file_id for file in files] == ["file-b", "file-c", "file-a"]
    assert [file.status for file in files] == ["processing", "failed", "ready"]
    assert files[0].file_name == "pending.txt"
    assert files[0].created_at == newer
    assert files[0].error_message is None
    assert files[1].error_message == "Embedding failed."


def test_get_files_does_not_commit_callers_transaction(sessions):
    with sessions() as session:
        create_file(session, "file-1", "notes.txt")
        assert len(get_files(session)) == 1
        session.rollback()

    with sessions() as reader:
        assert get_files(reader) == []


def test_get_files_returns_data_independent_of_orm_records(sessions):
    with sessions.begin() as session:
        create_file(session, "file-1", "notes.txt")

    with sessions.begin() as session:
        files = get_files(session)
        files[0].file_name = "local-change.txt"

    with sessions() as reader:
        assert get_files(reader)[0].file_name == "notes.txt"


def test_get_file_returns_the_requested_file_as_a_snapshot(sessions):
    with sessions.begin() as session:
        create_file(session, "file-1", "first.txt")
        create_file(session, "file-2", "second.txt")

    with sessions() as session:
        file = get_file(session, "file-2")

    assert isinstance(file, FileInfo)
    assert file.file_id == "file-2"
    assert file.file_name == "second.txt"
    assert file.status == "processing"


def test_get_file_returns_none_for_missing_file(sessions):
    with sessions() as session:
        assert get_file(session, "missing") is None


def test_save_and_get_chunks_preserve_source_data_and_order(sessions):
    chunks = split_text("  café🙂\nmore notes  ", "file-1", 8, 2)
    other_chunks = split_text("Other material", "file-2")
    with sessions.begin() as session:
        create_file(session, "file-1", "notes.txt")
        create_file(session, "file-2", "other.txt")
        save_chunks(session, list(reversed(chunks)))
        save_chunks(session, other_chunks)

    with sessions() as reader:
        stored = get_chunks(reader, "file-1")
        assert get_file(reader, "file-1").status == "processing"

    assert all(isinstance(chunk, Chunk) for chunk in stored)
    assert stored == chunks


def test_empty_chunks_and_missing_files_return_empty_lists(sessions):
    with sessions.begin() as session:
        create_file(session, "file-1", "notes.txt")
        save_chunks(session, [])
        assert get_chunks(session, "file-1") == []
        assert get_chunks(session, "missing") == []


def test_save_chunks_rejects_missing_parent(sessions):
    with sessions() as session:
        with pytest.raises(IntegrityError):
            save_chunks(session, split_text("abc", "missing"))
        session.rollback()


def test_save_chunks_duplicate_failure_rolls_back_the_batch(sessions):
    chunks = split_text("abcdefghij", "file-1", 6, 2)
    with sessions.begin() as session:
        create_file(session, "file-1", "notes.txt")

    with sessions() as session:
        with pytest.raises(IntegrityError):
            save_chunks(session, [*chunks, chunks[0]])
        session.rollback()

    with sessions() as reader:
        assert get_chunks(reader, "file-1") == []


@pytest.mark.parametrize("status", ["processing", "ready", "failed"])
def test_update_file_status_preserves_other_file(sessions, status):
    error = "Embedding failed." if status == "failed" else None
    with sessions.begin() as session:
        create_file(session, "file-1", "notes.txt")
        create_file(session, "file-2", "other.txt")
        update_file_status(session, "file-1", status, error)

    with sessions() as reader:
        file = get_file(reader, "file-1")
        assert file.status == status
        assert file.error_message == error
        assert get_file(reader, "file-2").status == "processing"


def test_update_file_status_clears_previous_error(sessions):
    with sessions.begin() as session:
        create_file(session, "file-1", "notes.txt")
        update_file_status(session, "file-1", "failed", "Embedding failed.")
    with sessions.begin() as session:
        update_file_status(session, "file-1", "processing")

    with sessions() as reader:
        assert get_file(reader, "file-1").error_message is None


def test_update_missing_file_raises_lookup_error(sessions):
    with sessions() as session:
        with pytest.raises(LookupError, match="missing"):
            update_file_status(session, "missing", "ready")


def test_update_file_status_rejects_invalid_status(sessions):
    with sessions.begin() as session:
        create_file(session, "file-1", "notes.txt")
    with sessions() as session:
        with pytest.raises(IntegrityError):
            update_file_status(session, "file-1", "unknown")
        session.rollback()
        assert get_file(session, "file-1").status == "processing"


def test_chunk_writes_and_status_updates_share_callers_transaction(sessions):
    with sessions.begin() as session:
        create_file(session, "file-1", "notes.txt")
    with sessions() as session:
        save_chunks(session, split_text("abc", "file-1"))
        update_file_status(session, "file-1", "ready")
        assert len(get_chunks(session, "file-1")) == 1
        assert get_file(session, "file-1").status == "ready"
        session.rollback()

    with sessions() as reader:
        assert get_chunks(reader, "file-1") == []
        assert get_file(reader, "file-1").status == "processing"


@pytest.mark.parametrize("commit", [True, False])
def test_deletion_obeys_callers_transaction_and_preserves_other_files(sessions, commit):
    first = split_text("First. Second.", "file-1", chunk_size=7, overlap=0)
    second = split_text("Keep.", "file-2")
    with sessions.begin() as session:
        create_file(session, "file-1", "notes.txt")
        create_file(session, "file-2", "notes.txt")
        save_chunks(session, first + second)

    with sessions() as session:
        delete_chunks(session, "file-1")
        assert get_chunks(session, "file-1") == []
        assert get_file(session, "file-1") is not None
        delete_file_record(session, "file-1")
        assert get_file(session, "file-1") is None
        if commit:
            session.commit()
        else:
            session.rollback()

    with sessions() as reader:
        assert get_chunks(reader, "file-1") == ([] if commit else first)
        assert (get_file(reader, "file-1") is None) == commit
        assert get_chunks(reader, "file-2") == second
        assert get_file(reader, "file-2").file_name == "notes.txt"


def test_delete_chunks_is_repeatable_and_missing_file_record_raises(sessions):
    with sessions.begin() as session:
        create_file(session, "file-1", "notes.txt")
        save_chunks(session, split_text("Notes.", "file-1"))
        delete_chunks(session, "file-1")
        delete_chunks(session, "file-1")
        delete_chunks(session, "missing")
        delete_file_record(session, "file-1")
        with pytest.raises(LookupError, match="missing"):
            delete_file_record(session, "missing")
