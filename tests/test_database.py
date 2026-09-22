import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from knowledgebase.storage.database import (
    build_engine,
    build_session_factory,
    init_db,
)
from knowledgebase.storage.models import ChunkRecord, FileRecord


def test_build_engine_does_not_create_database_until_used(tmp_path):
    path = tmp_path / "knowledgebase.db"
    engine = build_engine(f"sqlite:///{path}")
    try:
        assert not path.exists()
        init_db(engine)
        assert path.exists()
        assert set(inspect(engine).get_table_names()) == {
            "files", "chunks", "conversations", "messages", "answer_snapshots",
            "document_sources", "chunk_structures",
        }
    finally:
        engine.dispose()


def test_init_db_preserves_existing_data(engine):
    init_db(engine)
    session_factory = build_session_factory(engine)
    with session_factory.begin() as session:
        session.add(FileRecord(file_id="file-1", file_name="notes.txt"))

    init_db(engine)

    with session_factory() as session:
        assert session.get(FileRecord, "file-1").file_name == "notes.txt"


def test_foreign_keys_are_enabled_on_each_new_connection(engine):
    with engine.connect() as first, engine.connect() as second:
        assert first.connection.driver_connection is not second.connection.driver_connection
        assert first.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
        assert second.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1

    engine.dispose()
    with engine.connect() as replacement:
        assert replacement.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1


def test_session_factory_persists_data_across_sessions_and_connections(engine):
    init_db(engine)
    session_factory = build_session_factory(engine)
    with session_factory.begin() as writer:
        writer.add(FileRecord(file_id="file-1", file_name="notes.txt"))

    engine.dispose()

    with session_factory() as reader:
        assert reader is not writer
        assert reader.get(FileRecord, "file-1").file_name == "notes.txt"


def test_transaction_context_rolls_back_on_error(engine):
    init_db(engine)
    session_factory = build_session_factory(engine)
    with pytest.raises(RuntimeError, match="Processing failed"):
        with session_factory.begin() as session:
            session.add(FileRecord(file_id="file-1", file_name="notes.txt"))
            session.flush()
            raise RuntimeError("Processing failed")

    with session_factory() as reader:
        assert reader.get(FileRecord, "file-1") is None


def test_session_rejects_chunks_without_a_parent_file(engine):
    init_db(engine)
    session_factory = build_session_factory(engine)
    with pytest.raises(IntegrityError):
        with session_factory.begin() as session:
            session.add(
                ChunkRecord(
                    chunk_id="missing:0", file_id="missing", text="abc",
                    index=0, start_offset=0, end_offset=3,
                )
            )


def test_in_memory_database_is_supported():
    engine = build_engine("sqlite:///:memory:")
    try:
        init_db(engine)
        session_factory = build_session_factory(engine)
        with session_factory.begin() as session:
            session.add(FileRecord(file_id="file-1", file_name="notes.txt"))
        with session_factory() as reader:
            assert reader.get(FileRecord, "file-1").status == "processing"
    finally:
        engine.dispose()
