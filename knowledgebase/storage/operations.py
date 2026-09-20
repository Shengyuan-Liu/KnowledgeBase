from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from knowledgebase.schemas import Chunk, FileInfo
from knowledgebase.storage.models import ChunkRecord, FileRecord


def create_file(session: Session, file_id: str, file_name: str) -> None:
    """Insert a processing file; the caller owns commit and rollback.

    Flush immediately so database defaults and constraints are applied.
    """
    record = FileRecord(file_id=file_id, file_name=file_name)
    session.add(record)
    session.flush()


def get_files(session: Session) -> list[FileInfo]:
    """Return all files newest first, breaking timestamp ties by file ID.

    Results are data snapshots independent of the session. The caller retains
    ownership of the transaction.
    """
    statement = select(FileRecord).order_by(
        FileRecord.created_at.desc(), FileRecord.file_id.asc()
    )
    return [
        FileInfo.model_validate(record, from_attributes=True)
        for record in session.scalars(statement)
    ]


def get_file(session: Session, file_id: str) -> FileInfo | None:
    """Return one file as a data snapshot, or None if it does not exist."""
    record = session.get(FileRecord, file_id)
    if record is None:
        return None
    return FileInfo.model_validate(record, from_attributes=True)


def save_chunks(session: Session, chunks: list[Chunk]) -> None:
    """Insert chunks and check constraints without committing or marking ready.

    Duplicate IDs or file/index pairs raise IntegrityError; existing chunks are
    not overwritten. The caller must roll back a failed transaction.
    """
    if not chunks:
        return
    session.add_all(ChunkRecord(**chunk.model_dump()) for chunk in chunks)
    session.flush()


def get_chunks(session: Session, file_id: str) -> list[Chunk]:
    """Return a file's chunks ordered by index, or an empty list.

    This storage query does not filter file status. Retrieval must separately
    ensure that a file is ready before using its chunks as answer evidence.
    """
    statement = (
        select(ChunkRecord)
        .where(ChunkRecord.file_id == file_id)
        .order_by(ChunkRecord.index)
    )
    return [
        Chunk.model_validate(record, from_attributes=True)
        for record in session.scalars(statement)
    ]


def get_chunks_by_ids(session: Session, chunk_ids: list[str]) -> list[Chunk]:
    """Load existing chunks by ID; the query does not preserve requested order."""
    statement = select(ChunkRecord).where(ChunkRecord.chunk_id.in_(chunk_ids))
    return [
        Chunk.model_validate(record, from_attributes=True)
        for record in session.scalars(statement)
    ]


def update_file_status(
    session: Session,
    file_id: str,
    status: str,
    error_message: str | None = None,
) -> None:
    """Update status and error details without committing.

    A missing file raises LookupError; an invalid status raises IntegrityError
    during flush. Omitting error_message clears any previous error. The caller
    decides when ingestion has completed and a file may become ready.
    """
    record = session.get(FileRecord, file_id)
    if record is None:
        raise LookupError(f"File not found: {file_id}")
    record.status = status
    record.error_message = error_message
    session.flush()


def delete_chunks(session: Session, file_id: str) -> None:
    """Delete a file's chunks; the caller owns commit and rollback.

    No matching chunks is a no-op, including after an earlier cleanup attempt.
    """
    session.execute(delete(ChunkRecord).where(ChunkRecord.file_id == file_id))
    session.flush()


def delete_file_record(session: Session, file_id: str) -> None:
    """Delete an existing file record after its chunks have been removed.

    A missing file raises LookupError. Flush without committing so the caller
    can keep chunk and file deletion in the same transaction.
    """
    record = session.get(FileRecord, file_id)
    if record is None:
        raise LookupError(f"File not found: {file_id}")
    session.delete(record)
    session.flush()
