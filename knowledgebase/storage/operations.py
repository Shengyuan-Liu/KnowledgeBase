from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from knowledgebase.schemas import Chunk, ConversationInfo, FileInfo, MessageInfo
from knowledgebase.storage.models import (
    ChunkRecord,
    ConversationRecord,
    FileRecord,
    MessageRecord,
)


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


def create_conversation(session: Session, conversation_id: str) -> None:
    """Insert a conversation and flush without committing the caller's work."""
    session.add(ConversationRecord(conversation_id=conversation_id))
    session.flush()


def get_conversation(session: Session, conversation_id: str) -> ConversationInfo | None:
    """Return conversation metadata, or None when the ID does not exist."""
    record = session.get(ConversationRecord, conversation_id)
    if record is None:
        return None
    return ConversationInfo.model_validate(record, from_attributes=True)


def save_message(
    session: Session, conversation_id: str, role: str, content: str
) -> MessageInfo:
    """Append a user/assistant message, returning its generated ID and timestamp.

    Flush without committing. The database enforces the conversation foreign key
    and supported roles. Preserve content unchanged; the caller owns rollback.
    """
    record = MessageRecord(conversation_id=conversation_id, role=role, content=content)
    session.add(record)
    session.flush()
    return MessageInfo.model_validate(record, from_attributes=True)


def get_messages(
    session: Session, conversation_id: str, limit: int | None = None
) -> list[MessageInfo]:
    """Read one conversation in append order, optionally only its latest messages.

    A positive limit counts individual messages, not complete exchanges. Results
    still run oldest to newest. Empty and unknown conversations return an empty
    list; get_conversation distinguishes them. Reads do not commit.
    """
    if limit is not None and limit < 1:
        raise ValueError("limit must be positive or None.")
    statement = (
        select(MessageRecord)
        .where(MessageRecord.conversation_id == conversation_id)
        .order_by(MessageRecord.message_id.desc())
    )
    if limit is not None:
        statement = statement.limit(limit)
    return [
        MessageInfo.model_validate(record, from_attributes=True)
        for record in reversed(session.scalars(statement).all())
    ]
