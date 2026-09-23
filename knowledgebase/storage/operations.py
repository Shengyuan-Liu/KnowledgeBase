from hashlib import sha256
from typing import Literal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from knowledgebase.schemas import (
    ChatAnswer, ChildChunk, Chunk, ConversationDetail, ConversationInfo, ConversationMessage,
    DocumentSource, FileInfo, HistoricalSource, MessageInfo, ParentChildChunks, ParentChunk,
    SourceBlock, StructuredChunk,
)
from knowledgebase.storage.models import (
    AnswerSnapshotRecord,
    ChildParentRecord,
    ChunkRecord,
    ChunkStructureRecord,
    ConversationRecord,
    DocumentSourceRecord,
    FileRecord,
    MessageRecord,
    ParentChunkRecord,
    RetrievalSnapshotRecord,
)


class FileRecordNotFoundError(LookupError):
    """A requested file record does not exist in business storage."""


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


def save_document_source(
    session: Session, file_id: str, source_format: Literal["txt", "md"],
    text: str, blocks: list[SourceBlock],
) -> None:
    """Insert the unchanged source and its ordered parser output without committing.

    The hash is SHA-256 of the decoded source encoded as UTF-8, with no newline
    normalization. The caller supplies blocks parsed from this exact text.
    Duplicate or missing file IDs are enforced by the database.
    """
    session.add(DocumentSourceRecord(
        file_id=file_id, source_format=source_format, text=text,
        source_hash=sha256(text.encode("utf-8")).hexdigest(),
        blocks=[block.model_dump(mode="json") for block in blocks],
    ))
    session.flush()


def get_document_source(session: Session, file_id: str) -> DocumentSource | None:
    """Return a source snapshot, or None for missing files and MVP-only records."""
    record = session.get(DocumentSourceRecord, file_id)
    if record is None:
        return None
    return DocumentSource.model_validate(record, from_attributes=True)


def save_chunks(session: Session, chunks: list[Chunk]) -> None:
    """Insert chunks and check constraints without committing or marking ready.

    StructuredChunk inputs also persist their metadata and token configuration.
    ChildChunk inputs additionally link to an existing parent. Use
    save_parent_child_chunks to insert new parents and their children together.
    Duplicate IDs or file/index pairs raise IntegrityError; existing chunks are
    not overwritten. The caller must roll back a failed transaction.
    """
    if not chunks:
        return
    session.add_all(
        ChunkRecord(**chunk.model_dump(include=set(Chunk.model_fields))) for chunk in chunks
    )
    session.flush()
    session.add_all(
        ChunkStructureRecord(
            chunk_id=chunk.chunk_id,
            **chunk.model_dump(include=set(StructuredChunk.model_fields) - set(Chunk.model_fields)),
        )
        for chunk in chunks if isinstance(chunk, StructuredChunk)
    )
    session.flush()
    session.add_all(
        ChildParentRecord(chunk_id=chunk.chunk_id, parent_id=chunk.parent_id)
        for chunk in chunks if isinstance(chunk, ChildChunk)
    )
    session.flush()


def save_parent_child_chunks(session: Session, chunks: ParentChildChunks) -> None:
    """Insert parents before children; flush without committing the caller's work.

    Supply the output of split_parent_child for the same canonical source.
    The splitter owns source containment and same-file membership; storage retains
    that output and enforces record identities and references with foreign keys.
    """
    session.add_all(ParentChunkRecord(**parent.model_dump()) for parent in chunks.parents)
    session.flush()
    save_chunks(session, chunks.children)


def get_parents(session: Session, file_id: str) -> list[ParentChunk]:
    """Return a file's parent snapshots in source order, without filtering status."""
    statement = select(ParentChunkRecord).where(ParentChunkRecord.file_id == file_id).order_by(ParentChunkRecord.index)
    return [ParentChunk.model_validate(record, from_attributes=True) for record in session.scalars(statement)]


def get_parents_by_ids(session: Session, parent_ids: list[str]) -> list[ParentChunk]:
    """Load existing parents once per ID; requested order is not preserved."""
    statement = select(ParentChunkRecord).where(ParentChunkRecord.parent_id.in_(parent_ids))
    return [ParentChunk.model_validate(record, from_attributes=True) for record in session.scalars(statement)]


def _chunk_snapshot(
    record: ChunkRecord, structure: ChunkStructureRecord | None, parent: ChildParentRecord | None,
) -> Chunk:
    """Restore the data model stored for this chunk, including optional v1 metadata."""
    chunk = Chunk.model_validate(record, from_attributes=True)
    if structure is None:
        return chunk
    structured = StructuredChunk(
        **chunk.model_dump(), heading_path=structure.heading_path,
        source_block_indices=structure.source_block_indices, token_count=structure.token_count,
        tokenizer=structure.tokenizer, max_tokens=structure.max_tokens,
    )
    if parent is not None:
        return ChildChunk(**structured.model_dump(), parent_id=parent.parent_id)
    return structured


def get_chunks(session: Session, file_id: str) -> list[Chunk]:
    """Return a file's chunks ordered by index, or an empty list.

    Child records return ChildChunk, flat structural records return StructuredChunk,
    and MVP records return Chunk.
    This storage query does not filter file status. Retrieval must separately
    ensure that a file is ready before using its chunks as answer evidence.
    """
    statement = (
        select(ChunkRecord, ChunkStructureRecord, ChildParentRecord)
        .outerjoin(ChunkStructureRecord, ChunkStructureRecord.chunk_id == ChunkRecord.chunk_id)
        .outerjoin(ChildParentRecord, ChildParentRecord.chunk_id == ChunkRecord.chunk_id)
        .where(ChunkRecord.file_id == file_id)
        .order_by(ChunkRecord.index)
    )
    return [
        _chunk_snapshot(record, structure, parent)
        for record, structure, parent in session.execute(statement)
    ]


def get_chunks_by_ids(session: Session, chunk_ids: list[str]) -> list[Chunk]:
    """Load existing chunks by ID; the query does not preserve requested order."""
    statement = (
        select(ChunkRecord, ChunkStructureRecord, ChildParentRecord)
        .outerjoin(ChunkStructureRecord, ChunkStructureRecord.chunk_id == ChunkRecord.chunk_id)
        .outerjoin(ChildParentRecord, ChildParentRecord.chunk_id == ChunkRecord.chunk_id)
        .where(ChunkRecord.chunk_id.in_(chunk_ids))
    )
    return [
        _chunk_snapshot(record, structure, parent)
        for record, structure, parent in session.execute(statement)
    ]


def update_file_status(
    session: Session,
    file_id: str,
    status: str,
    error_message: str | None = None,
) -> None:
    """Update status and error details without committing.

    A missing file raises FileRecordNotFoundError; an invalid status raises IntegrityError
    during flush. Omitting error_message clears any previous error. The caller
    decides when ingestion has completed and a file may become ready.
    """
    record = session.get(FileRecord, file_id)
    if record is None:
        raise FileRecordNotFoundError(f"File not found: {file_id}")
    record.status = status
    record.error_message = error_message
    session.flush()


def delete_chunks(session: Session, file_id: str) -> None:
    """Delete a file's flat/child chunks and parents; the caller owns the transaction.

    Structural metadata and parent links cascade from children before parents
    are removed. The canonical document source stays attached to the file.
    No matching chunks is a no-op, including after an earlier cleanup attempt.
    """
    session.execute(delete(ChunkRecord).where(ChunkRecord.file_id == file_id))
    session.execute(delete(ParentChunkRecord).where(ParentChunkRecord.file_id == file_id))
    session.flush()


def delete_file_record(session: Session, file_id: str) -> None:
    """Delete an existing file record after its chunks have been removed.

    The canonical document source and any childless parents cascade from the file.
    A missing file raises FileRecordNotFoundError. Flush without committing so the caller
    can keep chunk and file deletion in the same transaction.
    """
    record = session.get(FileRecord, file_id)
    if record is None:
        raise FileRecordNotFoundError(f"File not found: {file_id}")
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


def save_answer_snapshot(
    session: Session, message_id: int, retrieval_question: str, answer: ChatAnswer,
) -> None:
    """Save completed assistant evidence; the caller owns the exchange transaction."""
    session.add(AnswerSnapshotRecord(
        message_id=message_id,
        retrieval_question=retrieval_question,
        sources=[source.model_dump(mode="json") for source in answer.sources],
        citation_check=answer.citation_check.model_dump(mode="json"),
    ))
    session.flush()
    if answer.retrieval is not None:
        session.add(RetrievalSnapshotRecord(
            message_id=message_id, diagnostics=answer.retrieval.model_dump(mode="json"),
        ))
        session.flush()


def get_conversation_detail(session: Session, conversation_id: str) -> ConversationDetail | None:
    """Read ordered display history without retrieving or reconstructing evidence.

    Missing snapshots remain null, including old assistant messages. File deletion
    is checked against current file records; saved source text stays unchanged.
    Follow-up resolution continues to use the text-only get_messages function.
    """
    conversation = get_conversation(session, conversation_id)
    if conversation is None:
        return None
    rows = session.execute(
        select(MessageRecord, AnswerSnapshotRecord, RetrievalSnapshotRecord)
        .outerjoin(AnswerSnapshotRecord, AnswerSnapshotRecord.message_id == MessageRecord.message_id)
        .outerjoin(RetrievalSnapshotRecord, RetrievalSnapshotRecord.message_id == MessageRecord.message_id)
        .where(MessageRecord.conversation_id == conversation_id)
        .order_by(MessageRecord.message_id)
    ).all()
    file_ids = {
        source["file_id"]
        for _, snapshot, _ in rows if snapshot is not None
        for source in snapshot.sources
    }
    existing_ids = set(session.scalars(select(FileRecord.file_id).where(FileRecord.file_id.in_(file_ids))))
    messages = []
    for record, snapshot, retrieval in rows:
        if snapshot is None:
            message = ConversationMessage.model_validate(record, from_attributes=True)
        else:
            message = ConversationMessage(
                **MessageInfo.model_validate(record, from_attributes=True).model_dump(),
                retrieval_question=snapshot.retrieval_question,
                sources=[HistoricalSource(**source, file_deleted=source["file_id"] not in existing_ids)
                         for source in snapshot.sources],
                citation_check=snapshot.citation_check,
                retrieval=retrieval.diagnostics if retrieval is not None else None,
            )
        messages.append(message)
    return ConversationDetail(**conversation.model_dump(), messages=messages)
