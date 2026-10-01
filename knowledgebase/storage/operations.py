from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Literal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from knowledgebase.schemas import (
    ChatAnswer, Chunk, ChunkBatch, File, SourceBlock, ConversationDetail,
    ConversationInfo, ConversationMessage, HistoricalSource, MessageInfo,
)

from knowledgebase.storage.models import (
    AnswerSnapshotRecord,
    ChildParentRecord,
    ChunkRecord,
    ChunkStructureRecord,
    ConversationRecord,
    DocumentSourceRecord,
    DocumentIndexRecord,
    FileRecord,
    PdfSourceRecord,
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


def _file_snapshot(record: FileRecord, pdf=None) -> File:
    values = {name: getattr(record, name) for name in FileRecord.__table__.columns.keys()}
    values["type"] = Path(record.file_name).suffix.lower().lstrip(".")
    if pdf is not None:
        values.update(page_count=pdf.page_count, warnings=pdf.warnings)
    return File(**values)


def get_files(session: Session) -> list[File]:
    """Read metadata without loading document text or PDF geometry."""
    rows = session.execute(select(FileRecord, PdfSourceRecord.page_count, PdfSourceRecord.warnings)
                           .outerjoin(PdfSourceRecord, PdfSourceRecord.file_id == FileRecord.file_id)
                           .order_by(FileRecord.created_at.desc(), FileRecord.file_id.asc()))
    return [_file_snapshot(row[0], row if row.page_count is not None else None) for row in rows]


def get_file(session: Session, file_id: str) -> File | None:
    record = session.get(FileRecord, file_id)
    return _file_snapshot(record, session.get(PdfSourceRecord, file_id)) if record is not None else None


def get_source_texts(session: Session, file_ids: list[str]) -> dict[str, str]:
    """Load canonical text for identity resolution without deserializing blocks."""
    texts = dict(session.execute(select(DocumentSourceRecord.file_id, DocumentSourceRecord.text)
                                .where(DocumentSourceRecord.file_id.in_(file_ids))).all())
    texts.update(session.execute(select(PdfSourceRecord.file_id, PdfSourceRecord.extraction["text"].as_string())
                                 .where(PdfSourceRecord.file_id.in_(file_ids))).all())
    return texts


def save_document_source(
    session: Session, file_id: str, source_format: Literal["txt", "md"],
    text: str, blocks: list[SourceBlock], *, indexing: dict | None = None,
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

    if indexing is not None:
        session.add(DocumentIndexRecord(file_id=file_id, details=indexing))
        session.flush()


def get_document_source(session: Session, file_id: str) -> File | None:
    """Load parsed content using the existing on-disk tables."""
    record = session.get(DocumentSourceRecord, file_id)
    if record is None:
        return get_pdf_extraction(session, file_id)
    metadata = get_file(session, file_id)
    indexing = session.get(DocumentIndexRecord, file_id)
    return metadata.model_copy(update={
        "text": record.text, "source_hash": record.source_hash,
        "blocks": tuple(SourceBlock.model_validate(b) for b in record.blocks),
        "indexing": deepcopy(indexing.details) if indexing is not None else None,
    })


def save_chunks(session: Session, chunks: list[Chunk]) -> None:
    """Insert chunks and check constraints without committing or marking ready.

    Structured spans retain their token metadata; child spans link to a parent. Use
    save_parent_child_chunks to insert new parents and their children together.
    Duplicate IDs or file/index pairs raise IntegrityError; existing chunks are
    not overwritten. The caller must roll back a failed transaction.
    """
    if not chunks:
        return
    session.add_all(
        ChunkRecord(**chunk.model_dump(include=set(ChunkRecord.__table__.columns.keys()))) for chunk in chunks
    )
    session.flush()
    session.add_all(
        ChunkStructureRecord(**chunk.model_dump(include=set(ChunkStructureRecord.__table__.columns.keys())))
        for chunk in chunks if chunk.token_count is not None
    )
    session.flush()
    session.add_all(
        ChildParentRecord(chunk_id=chunk.chunk_id, parent_id=chunk.parent_id)
        for chunk in chunks if chunk.type == "child"
    )
    session.flush()


def save_parent_child_chunks(session: Session, chunks: ChunkBatch) -> None:
    """Persist parent spans before their indexed children in the caller's transaction."""
    fields = set(ParentChunkRecord.__table__.columns.keys()) - {"parent_id"}
    session.add_all(ParentChunkRecord(parent_id=parent.chunk_id, **parent.model_dump(include=fields))
                    for parent in chunks.parents)
    session.flush()
    save_chunks(session, chunks.children)


def _parent_snapshot(record: ParentChunkRecord) -> Chunk:
    fields = set(ParentChunkRecord.__table__.columns.keys()) - {"parent_id"}
    return Chunk(chunk_id=record.parent_id, type="parent", **{name: getattr(record, name) for name in fields})


def get_parents(session: Session, file_id: str) -> list[Chunk]:
    """Return a file's parent spans in source order."""
    statement = select(ParentChunkRecord).where(ParentChunkRecord.file_id == file_id).order_by(ParentChunkRecord.index)
    return [_parent_snapshot(record) for record in session.scalars(statement)]


def get_parents_by_ids(session: Session, parent_ids: list[str]) -> list[Chunk]:
    """Load existing parents once per ID; requested order is not preserved."""
    statement = select(ParentChunkRecord).where(ParentChunkRecord.parent_id.in_(parent_ids))
    return [_parent_snapshot(record) for record in session.scalars(statement)]


def _chunk_snapshot(
    record: ChunkRecord, structure: ChunkStructureRecord | None, parent: ChildParentRecord | None,
) -> Chunk:
    values = {name: getattr(record, name) for name in ChunkRecord.__table__.columns.keys()}
    if structure is not None:
        values.update({name: getattr(structure, name) for name in ChunkStructureRecord.__table__.columns.keys()})
    if parent is not None:
        values.update(type="child", parent_id=parent.parent_id)
    return Chunk(**values)


def get_chunks(session: Session, file_id: str) -> list[Chunk]:
    """Return a file's chunks ordered by index, or an empty list.

    This storage query does not filter file status. Retrieval must separately
    ensure that a file is ready before using its chunks as answer evidence.
    """
    return _read_chunks(session, ChunkRecord.file_id == file_id, order_by=(ChunkRecord.index,))


def get_chunks_by_ids(session: Session, chunk_ids: list[str]) -> list[Chunk]:
    """Load existing chunks by ID; the query does not preserve requested order."""
    return _read_chunks(session, ChunkRecord.chunk_id.in_(chunk_ids))


def get_chunks_for_files(session: Session, file_ids: list[str]) -> list[Chunk]:
    """Load the lexical corpus for the caller's eligible files in one query."""
    return _read_chunks(session, ChunkRecord.file_id.in_(file_ids),
                        order_by=(ChunkRecord.file_id, ChunkRecord.index))


def _read_chunks(session: Session, condition, *, order_by=()) -> list[Chunk]:
    """Use the same joins and snapshot conversion for every chunk lookup."""
    statement = (
        select(ChunkRecord, ChunkStructureRecord, ChildParentRecord)
        .outerjoin(ChunkStructureRecord, ChunkStructureRecord.chunk_id == ChunkRecord.chunk_id)
        .outerjoin(ChildParentRecord, ChildParentRecord.chunk_id == ChunkRecord.chunk_id)
        .where(condition)
        .order_by(*order_by)
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


def get_pdf_extraction(session: Session, file_id: str) -> File | None:
    record = session.get(PdfSourceRecord, file_id)
    if record is None:
        return None
    metadata = get_file(session, file_id)
    return File.model_validate({**record.extraction, **metadata.model_dump(exclude_unset=True),
                                "indexing": deepcopy(record.indexing)})


def save_pdf_source(session: Session, file_id: str, extraction, indexing: dict) -> None:
    session.add(PdfSourceRecord(
        file_id=file_id, revision_id=extraction.revision_id, source_hash=extraction.source_hash,
        page_count=extraction.page_count, warnings=[w.model_dump(mode="json") for w in extraction.warnings],
        extraction=extraction.extraction_data(), indexing=indexing,
    ))
    session.flush()


def delete_pdf_source(session: Session, file_id: str) -> None:
    session.execute(delete(PdfSourceRecord).where(PdfSourceRecord.file_id == file_id))
    session.flush()
