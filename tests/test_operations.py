from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from knowledgebase.storage.database import (
    build_engine,
    build_session_factory,
    init_db,
)
from knowledgebase.rag.chunking import split_text
from knowledgebase.storage.models import FileRecord
from knowledgebase.schemas import Chunk, FileInfo
from knowledgebase.storage.operations import (
    create_file,
    get_file,
    get_files,
    get_chunks,
    save_chunks,
    update_file_status,
)


@pytest.fixture
def session_factory(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'operations.db'}")
    try:
        init_db(engine)
        yield build_session_factory(engine)
    finally:
        engine.dispose()


def test_create_file_flushes_record_with_defaults(session_factory):
    with session_factory() as session:
        result = create_file(session, "file-1", "notes.txt")

        with session.no_autoflush:
            record = session.scalars(select(FileRecord)).one()
        assert result is None
        assert record.file_id == "file-1"
        assert record.file_name == "notes.txt"
        assert record.status == "processing"
        assert record.error_message is None
        assert isinstance(record.created_at, datetime)


def test_create_file_persists_when_caller_commits(session_factory):
    with session_factory.begin() as session:
        create_file(session, "file-1", "notes.txt")

    with session_factory() as reader:
        assert reader.get(FileRecord, "file-1").file_name == "notes.txt"


def test_create_file_can_be_rolled_back_by_caller(session_factory):
    with session_factory() as session:
        create_file(session, "file-1", "notes.txt")
        session.rollback()

    with session_factory() as reader:
        assert reader.get(FileRecord, "file-1") is None


def test_create_file_rejects_duplicate_id_during_call(session_factory):
    with session_factory.begin() as session:
        create_file(session, "file-1", "original.txt")

    with session_factory() as session:
        with pytest.raises(IntegrityError):
            create_file(session, "file-1", "replacement.txt")
        session.rollback()
        assert session.get(FileRecord, "file-1").file_name == "original.txt"


def test_get_files_returns_empty_list(session_factory):
    with session_factory() as session:
        assert get_files(session) == []


def test_get_files_returns_all_statuses_in_stable_newest_first_order(session_factory):
    older = datetime(2026, 1, 1)
    newer = datetime(2026, 1, 2)
    with session_factory.begin() as session:
        session.add_all([
            FileRecord(file_id="file-c", file_name="failed.txt", status="failed",
                       error_message="Embedding failed.", created_at=newer),
            FileRecord(file_id="file-a", file_name="ready.txt", status="ready",
                       created_at=older),
            FileRecord(file_id="file-b", file_name="pending.txt", status="processing",
                       created_at=newer),
        ])

    with session_factory() as session:
        files = get_files(session)

    assert all(isinstance(file, FileInfo) for file in files)
    assert [file.file_id for file in files] == ["file-b", "file-c", "file-a"]
    assert [file.status for file in files] == ["processing", "failed", "ready"]
    assert files[0].file_name == "pending.txt"
    assert files[0].created_at == newer
    assert files[0].error_message is None
    assert files[1].error_message == "Embedding failed."


def test_get_files_does_not_commit_callers_transaction(session_factory):
    with session_factory() as session:
        create_file(session, "file-1", "notes.txt")
        assert len(get_files(session)) == 1
        session.rollback()

    with session_factory() as reader:
        assert get_files(reader) == []


def test_get_files_returns_data_independent_of_orm_records(session_factory):
    with session_factory.begin() as session:
        create_file(session, "file-1", "notes.txt")

    with session_factory.begin() as session:
        files = get_files(session)
        files[0].file_name = "local-change.txt"

    with session_factory() as reader:
        assert get_files(reader)[0].file_name == "notes.txt"


def test_get_file_returns_the_requested_file_as_a_snapshot(session_factory):
    with session_factory.begin() as session:
        create_file(session, "file-1", "first.txt")
        create_file(session, "file-2", "second.txt")

    with session_factory() as session:
        file = get_file(session, "file-2")

    assert isinstance(file, FileInfo)
    assert file.file_id == "file-2"
    assert file.file_name == "second.txt"
    assert file.status == "processing"


def test_get_file_returns_none_for_missing_file(session_factory):
    with session_factory() as session:
        assert get_file(session, "missing") is None


def test_save_and_get_chunks_preserve_source_data_and_order(session_factory):
    chunks = split_text("  café🙂\nmore notes  ", "file-1", 8, 2)
    other_chunks = split_text("Other material", "file-2")
    with session_factory.begin() as session:
        create_file(session, "file-1", "notes.txt")
        create_file(session, "file-2", "other.txt")
        save_chunks(session, list(reversed(chunks)))
        save_chunks(session, other_chunks)

    with session_factory() as reader:
        stored = get_chunks(reader, "file-1")
        assert get_file(reader, "file-1").status == "processing"

    assert all(isinstance(chunk, Chunk) for chunk in stored)
    assert stored == chunks


def test_empty_chunks_and_missing_files_return_empty_lists(session_factory):
    with session_factory.begin() as session:
        create_file(session, "file-1", "notes.txt")
        save_chunks(session, [])
        assert get_chunks(session, "file-1") == []
        assert get_chunks(session, "missing") == []


def test_save_chunks_rejects_missing_parent(session_factory):
    with session_factory() as session:
        with pytest.raises(IntegrityError):
            save_chunks(session, split_text("abc", "missing"))
        session.rollback()


def test_save_chunks_duplicate_failure_rolls_back_the_batch(session_factory):
    chunks = split_text("abcdefghij", "file-1", 6, 2)
    with session_factory.begin() as session:
        create_file(session, "file-1", "notes.txt")

    with session_factory() as session:
        with pytest.raises(IntegrityError):
            save_chunks(session, [*chunks, chunks[0]])
        session.rollback()

    with session_factory() as reader:
        assert get_chunks(reader, "file-1") == []


@pytest.mark.parametrize("status", ["processing", "ready", "failed"])
def test_update_file_status_preserves_other_file(session_factory, status):
    error = "Embedding failed." if status == "failed" else None
    with session_factory.begin() as session:
        create_file(session, "file-1", "notes.txt")
        create_file(session, "file-2", "other.txt")
        update_file_status(session, "file-1", status, error)

    with session_factory() as reader:
        file = get_file(reader, "file-1")
        assert file.status == status
        assert file.error_message == error
        assert get_file(reader, "file-2").status == "processing"


def test_update_file_status_clears_previous_error(session_factory):
    with session_factory.begin() as session:
        create_file(session, "file-1", "notes.txt")
        update_file_status(session, "file-1", "failed", "Embedding failed.")
    with session_factory.begin() as session:
        update_file_status(session, "file-1", "processing")

    with session_factory() as reader:
        assert get_file(reader, "file-1").error_message is None


def test_update_missing_file_raises_lookup_error(session_factory):
    with session_factory() as session:
        with pytest.raises(LookupError, match="missing"):
            update_file_status(session, "missing", "ready")


def test_update_file_status_rejects_invalid_status(session_factory):
    with session_factory.begin() as session:
        create_file(session, "file-1", "notes.txt")
    with session_factory() as session:
        with pytest.raises(IntegrityError):
            update_file_status(session, "file-1", "unknown")
        session.rollback()
        assert get_file(session, "file-1").status == "processing"


def test_chunk_writes_and_status_updates_share_callers_transaction(session_factory):
    with session_factory.begin() as session:
        create_file(session, "file-1", "notes.txt")
    with session_factory() as session:
        save_chunks(session, split_text("abc", "file-1"))
        update_file_status(session, "file-1", "ready")
        assert len(get_chunks(session, "file-1")) == 1
        assert get_file(session, "file-1").status == "ready"
        session.rollback()

    with session_factory() as reader:
        assert get_chunks(reader, "file-1") == []
        assert get_file(reader, "file-1").status == "processing"
