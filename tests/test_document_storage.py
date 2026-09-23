from hashlib import sha256

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from knowledgebase.rag.chunking import split_structured, split_text
from knowledgebase.rag.parsing import parse_markdown, parse_txt
from knowledgebase.schemas import AnswerSource, ChatAnswer, Chunk, CitationCheck, StructuredChunk
from knowledgebase.services.files import delete_file
from knowledgebase.storage.database import build_session_factory, init_db
from knowledgebase.storage.models import (
    Base, ChunkRecord, ChunkStructureRecord, DocumentSourceRecord,
)
from knowledgebase.storage.operations import (
    create_conversation, create_file, delete_chunks, delete_file_record,
    get_chunks, get_chunks_by_ids, get_conversation_detail, get_document_source, get_file,
    save_answer_snapshot, save_chunks, save_document_source, save_message, update_file_status,
)


SOURCE = "# Guide\r\n\r\nA café 🙂 keeps its original spacing.\r\n\r\n## Setup\r\n\r\nInstall the package.\r\n"


def prepare(file_id="file-1", source_format="md"):
    blocks = parse_markdown(SOURCE) if source_format == "md" else parse_txt(SOURCE)
    chunks = split_structured(
        SOURCE, blocks, file_id, max_tokens=16, encoding_name="cl100k_base",
    )
    return blocks, chunks


def store_document(session, file_id="file-1", source_format="md"):
    blocks, chunks = prepare(file_id, source_format)
    create_file(session, file_id, f"notes.{source_format}")
    save_document_source(session, file_id, source_format, SOURCE, blocks)
    save_chunks(session, chunks)
    return blocks, chunks


@pytest.mark.parametrize("source_format", ["txt", "md"])
def test_source_and_structured_chunks_survive_reopening_database(engine, sessions, source_format):
    with sessions.begin() as session:
        expected_blocks, expected_chunks = store_document(session, source_format=source_format)
    engine.dispose()
    reopened = build_session_factory(engine)

    with reopened() as reader:
        source = get_document_source(reader, "file-1")
        chunks = get_chunks(reader, "file-1")
        assert get_file(reader, "file-1").status == "processing"

    assert source.file_id == "file-1"
    assert source.source_format == source_format
    assert source.text == SOURCE
    assert source.source_hash == sha256(SOURCE.encode("utf-8")).hexdigest()
    assert source.blocks == expected_blocks
    assert chunks == expected_chunks
    assert all(isinstance(chunk, StructuredChunk) for chunk in chunks)
    for chunk in chunks:
        assert chunk.text == source.text[chunk.start_offset:chunk.end_offset]
        assert chunk.tokenizer == "cl100k_base"
        assert chunk.max_tokens == 16
        assert all(
            source.blocks[index].start_offset < chunk.end_offset
            and source.blocks[index].end_offset > chunk.start_offset
            for index in chunk.source_block_indices
        )


def test_source_hash_distinguishes_original_line_endings(sessions):
    with sessions.begin() as session:
        for file_id, text in [("crlf", SOURCE), ("lf", SOURCE.replace("\r\n", "\n"))]:
            create_file(session, file_id, "notes.md")
            save_document_source(session, file_id, "md", text, parse_markdown(text))
        assert get_document_source(session, "crlf").source_hash != get_document_source(session, "lf").source_hash


def test_mixed_mvp_and_structured_chunks_preserve_their_types_and_metadata(sessions):
    blocks, structured = prepare()
    legacy = split_text("Legacy material.", "legacy")
    with sessions.begin() as session:
        create_file(session, "file-1", "notes.md")
        create_file(session, "legacy", "legacy.txt")
        save_document_source(session, "file-1", "md", SOURCE, blocks)
        save_chunks(session, list(reversed(structured)) + legacy)

    with sessions() as reader:
        assert get_chunks(reader, "file-1") == structured
        assert get_chunks(reader, "legacy") == legacy
        assert type(get_chunks(reader, "legacy")[0]) is Chunk
        assert get_document_source(reader, "legacy") is None
        assert get_document_source(reader, "missing") is None
        selected = get_chunks_by_ids(reader, [structured[-1].chunk_id, legacy[0].chunk_id, "missing"])
        assert {chunk.chunk_id: chunk for chunk in selected} == {
            structured[-1].chunk_id: structured[-1], legacy[0].chunk_id: legacy[0],
        }


def test_source_and_chunk_reads_are_detached_snapshots(sessions):
    with sessions.begin() as session:
        blocks, chunks = store_document(session)
    with sessions.begin() as session:
        source = get_document_source(session, "file-1")
        stored_chunks = get_chunks(session, "file-1")
        source.text = "Local mutation."
        source.blocks[0].heading_path.clear()
        source.blocks[0].text = "Changed heading."
        stored_chunks[0].heading_path.clear()
        stored_chunks[0].source_block_indices.clear()
    with sessions() as reader:
        assert get_document_source(reader, "file-1").text == SOURCE
        assert get_document_source(reader, "file-1").blocks == blocks
        assert get_chunks(reader, "file-1") == chunks


def test_source_chunk_metadata_and_ready_status_share_callers_transaction(sessions):
    with sessions.begin() as session:
        create_file(session, "file-1", "notes.md")
    blocks, chunks = prepare()
    with sessions() as session:
        save_document_source(session, "file-1", "md", SOURCE, blocks)
        save_chunks(session, chunks)
        update_file_status(session, "file-1", "ready")
        assert get_document_source(session, "file-1").blocks == blocks
        assert get_chunks(session, "file-1") == chunks
        session.rollback()

    with sessions() as reader:
        assert get_document_source(reader, "file-1") is None
        assert get_chunks(reader, "file-1") == []
        assert get_file(reader, "file-1").status == "processing"
        assert reader.scalars(select(ChunkStructureRecord)).all() == []


def test_duplicate_source_does_not_replace_original_document(sessions):
    with sessions.begin() as session:
        store_document(session)
    with sessions() as session:
        with pytest.raises(IntegrityError):
            save_document_source(session, "file-1", "txt", "Replacement.", parse_txt("Replacement."))
        session.rollback()
        assert get_document_source(session, "file-1").text == SOURCE
        assert get_document_source(session, "file-1").source_format == "md"


def test_source_requires_a_file_record(sessions):
    with sessions() as session:
        with pytest.raises(IntegrityError):
            save_document_source(session, "missing", "md", SOURCE, parse_markdown(SOURCE))
        session.rollback()


def test_duplicate_chunk_batch_rolls_back_source_and_metadata(sessions):
    blocks, chunks = prepare()
    with sessions.begin() as session:
        create_file(session, "file-1", "notes.md")
    with pytest.raises(IntegrityError):
        with sessions.begin() as session:
            save_document_source(session, "file-1", "md", SOURCE, blocks)
            save_chunks(session, [*chunks, chunks[0]])
    with sessions() as reader:
        assert get_document_source(reader, "file-1") is None
        assert get_chunks(reader, "file-1") == []
        assert reader.scalars(select(ChunkStructureRecord)).all() == []


@pytest.mark.parametrize("commit", [True, False])
def test_deletion_cascades_are_scoped_and_transactional(sessions, commit):
    with sessions.begin() as session:
        _, removed_chunks = store_document(session)
        _, kept_chunks = store_document(session, "keep")
    with sessions() as session:
        delete_chunks(session, "file-1")
        assert session.scalars(select(ChunkStructureRecord)).all()
        assert session.get(ChunkStructureRecord, removed_chunks[0].chunk_id) is None
        assert get_document_source(session, "file-1") is not None
        delete_file_record(session, "file-1")
        assert get_document_source(session, "file-1") is None
        if commit:
            session.commit()
        else:
            session.rollback()

    with sessions() as reader:
        assert get_chunks(reader, "file-1") == ([] if commit else removed_chunks)
        assert (get_document_source(reader, "file-1") is None) == commit
        assert get_chunks(reader, "keep") == kept_chunks
        assert get_document_source(reader, "keep").text == SOURCE
        assert len(reader.scalars(select(ChunkStructureRecord)).all()) == (
            len(kept_chunks) if commit else len(kept_chunks) + len(removed_chunks)
        )


def test_failed_file_with_source_but_no_chunks_can_be_deleted(sessions):
    with sessions.begin() as session:
        create_file(session, "file-1", "notes.md")
        save_document_source(session, "file-1", "md", SOURCE, parse_markdown(SOURCE))
        update_file_status(session, "file-1", "failed", "Indexing failed.")
    with sessions.begin() as session:
        delete_chunks(session, "file-1")
        delete_file_record(session, "file-1")
    with sessions() as reader:
        assert get_file(reader, "file-1") is None
        assert get_document_source(reader, "file-1") is None


def test_init_db_adds_v1_tables_without_rewriting_mvp_records(engine):
    v1_names = {"document_sources", "chunk_structures", "parent_chunks", "child_parents"}
    Base.metadata.create_all(engine, tables=[
        table for table in Base.metadata.sorted_tables if table.name not in v1_names
    ])
    sessions = build_session_factory(engine)
    legacy_chunks = split_text("Original MVP text.", "legacy")
    with sessions.begin() as session:
        create_file(session, "legacy", "legacy.txt")
        session.add_all(ChunkRecord(**chunk.model_dump()) for chunk in legacy_chunks)
    columns_before = {
        name: [column["name"] for column in inspect(engine).get_columns(name)]
        for name in ("files", "chunks")
    }
    init_db(engine)
    init_db(engine)
    engine.dispose()

    assert v1_names <= set(inspect(engine).get_table_names())
    for name, columns in columns_before.items():
        assert [column["name"] for column in inspect(engine).get_columns(name)] == columns
    with sessions() as reader:
        assert get_chunks(reader, "legacy") == legacy_chunks
        assert get_document_source(reader, "legacy") is None
        assert reader.scalars(select(ChunkStructureRecord)).all() == []


def test_existing_delete_service_cleans_v1_records_and_preserves_answer_evidence(storage):
    sessions, store, collection = storage
    with sessions.begin() as session:
        _, chunks = store_document(session)
        store.upsert_chunks(chunks, [[1.0, 0.0] for _ in chunks])
        update_file_status(session, "file-1", "ready")
        create_conversation(session, "conversation-1")
        answer = ChatAnswer(
            answer="Saved answer. [1]",
            sources=[AnswerSource(
                source_id=1, file_id="file-1", file_name="notes.md",
                chunk_id=chunks[0].chunk_id, text=chunks[0].text, distance=0.0,
            )],
            citation_check=CitationCheck(
                valid_source_ids=[1], invalid_source_ids=[], no_citations=False,
            ),
        )
        message = save_message(session, "conversation-1", "assistant", answer.answer)
        save_answer_snapshot(session, message.message_id, "What does the guide say?", answer)

    delete_file("file-1", sessions, store)

    assert collection.count() == 0
    with sessions() as reader:
        assert get_file(reader, "file-1") is None
        assert get_document_source(reader, "file-1") is None
        assert get_chunks(reader, "file-1") == []
        assert reader.scalars(select(ChunkStructureRecord)).all() == []
        assert reader.scalars(select(DocumentSourceRecord)).all() == []
        saved = get_conversation_detail(reader, "conversation-1").messages[0]
        assert saved.sources[0].text == chunks[0].text
        assert saved.sources[0].file_deleted is True
