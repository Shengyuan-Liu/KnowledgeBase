from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from knowledgebase.rag.chunking import split_text
from knowledgebase.storage.models import Base, ChunkRecord, FileRecord


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            yield session
    finally:
        engine.dispose()


def test_file_defaults_are_persisted(session):
    before = datetime.now(UTC).replace(tzinfo=None)
    session.add(FileRecord(file_id="file-1", file_name="notes.txt"))
    session.commit()
    session.expunge_all()

    record = session.get(FileRecord, "file-1")

    assert record.file_name == "notes.txt"
    assert record.status == "processing"
    assert record.error_message is None
    assert isinstance(record.created_at, datetime)
    assert record.created_at.tzinfo is None
    assert before <= record.created_at <= datetime.now(UTC).replace(tzinfo=None)


@pytest.mark.parametrize("status", ["processing", "ready", "failed"])
def test_file_status_and_error_can_be_updated(session, status):
    record = FileRecord(file_id="file-1", file_name="notes.txt")
    session.add(record)
    session.commit()
    record.status = status
    record.error_message = "Embedding failed." if status == "failed" else None
    session.commit()
    session.expunge_all()

    saved = session.get(FileRecord, "file-1")

    assert saved.status == status
    assert saved.error_message == ("Embedding failed." if status == "failed" else None)


def test_invalid_file_status_is_rejected(session):
    session.add(FileRecord(file_id="file-1", file_name="notes.txt", status="unknown"))

    with pytest.raises(IntegrityError):
        session.commit()


def test_file_name_is_required(session):
    session.add(FileRecord(file_id="file-1"))

    with pytest.raises(IntegrityError):
        session.commit()


def test_duplicate_file_id_is_rejected(session):
    session.add(FileRecord(file_id="file-1", file_name="notes.txt"))
    session.commit()
    session.add(FileRecord(file_id="file-1", file_name="other.txt"))

    with pytest.raises(IntegrityError):
        session.commit()


def test_chunks_round_trip_with_source_offsets(session):
    text = "  café🙂\nmore notes  "
    chunks = split_text(text, "file-1", chunk_size=8, overlap=2)
    session.add(FileRecord(file_id="file-1", file_name="notes.txt"))
    session.commit()
    session.add_all(ChunkRecord(**chunk.model_dump(include=set(ChunkRecord.__table__.columns.keys()))) for chunk in chunks)
    session.commit()
    session.expunge_all()

    records = session.scalars(
        select(ChunkRecord)
        .where(ChunkRecord.file_id == "file-1")
        .order_by(ChunkRecord.index)
    ).all()

    assert len(records) == len(chunks)
    for record, chunk in zip(records, chunks):
        assert {field: getattr(record, field) for field in chunk.model_dump(include=set(ChunkRecord.__table__.columns.keys()))} == chunk.model_dump(include=set(ChunkRecord.__table__.columns.keys()))
        assert record.text == text[record.start_offset:record.end_offset]


@pytest.fixture
def stored_chunk(session):
    session.add(FileRecord(file_id="file-1", file_name="notes.txt"))
    session.commit()
    chunk = split_text("abc", "file-1")[0]
    session.add(ChunkRecord(**chunk.model_dump(include=set(ChunkRecord.__table__.columns.keys()))))
    session.commit()
    return chunk.model_dump(include=set(ChunkRecord.__table__.columns.keys()))


@pytest.mark.parametrize(
    "changes",
    [
        {"chunk_id": "file-1:0", "index": 1},
        {"index": 0},
        {"file_id": "missing-file"},
        {"index": -1},
        {"start_offset": -1},
        {"start_offset": 4, "end_offset": 3},
        {"start_offset": 3, "end_offset": 3},
        {"text": None},
    ],
    ids=[
        "duplicate-id", "duplicate-file-index", "missing-parent", "negative-index",
        "negative-start", "reversed-offsets", "empty-range", "missing-text",
    ],
)
def test_invalid_chunk_is_rejected(session, stored_chunk, changes):
    values = {**stored_chunk, "chunk_id": "file-1:1", "index": 1, **changes}
    session.add(ChunkRecord(**values))

    with pytest.raises(IntegrityError):
        session.commit()


def test_different_files_can_share_a_chunk_index(session, stored_chunk):
    session.add(FileRecord(file_id="file-2", file_name="other.txt"))
    session.commit()
    session.add(ChunkRecord(**{**stored_chunk, "chunk_id": "file-2:0", "file_id": "file-2"}))
    session.commit()

    assert session.get(ChunkRecord, "file-2:0").index == 0
