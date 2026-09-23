import pytest
from sqlalchemy import delete, inspect, select
from sqlalchemy.exc import IntegrityError

from knowledgebase.rag.chunking import split_parent_child, split_structured, split_text
from knowledgebase.rag.parsing import parse_markdown, parse_txt
from knowledgebase.schemas import (
    AnswerSource, ChatAnswer, ChildChunk, Chunk, CitationCheck, ParentChildChunks, StructuredChunk,
)
from knowledgebase.services.files import delete_file, recover_interrupted_files
from knowledgebase.storage.database import build_engine, build_session_factory, init_db
from knowledgebase.storage.models import (
    Base, ChildParentRecord, ChunkRecord, ChunkStructureRecord, ParentChunkRecord,
)
from knowledgebase.storage.operations import (
    create_conversation, create_file, delete_chunks, delete_file_record,
    get_chunks, get_chunks_by_ids, get_conversation_detail, get_document_source,
    get_file, get_parents, get_parents_by_ids, save_answer_snapshot, save_chunks,
    save_document_source, save_message, save_parent_child_chunks, update_file_status,
)


SOURCE = (
    "# Guide\r\n\r\nA café 🙂 keeps its original spacing.\r\n\r\n"
    "- Install the package.\r\n- Restart the server.\r\n\r\n"
    "## Setup\r\n\r\n" + "A complete sentence describes the configuration. " * 12
)


def prepare(file_id="file-1", source_format="md"):
    blocks = parse_markdown(SOURCE) if source_format == "md" else parse_txt(SOURCE)
    chunks = split_parent_child(
        SOURCE, blocks, file_id, parent_max_tokens=48, child_max_tokens=16,
        encoding_name="cl100k_base",
    )
    return blocks, chunks


def store_document(session, file_id="file-1", source_format="md"):
    blocks, chunks = prepare(file_id, source_format)
    create_file(session, file_id, f"notes.{source_format}")
    save_document_source(session, file_id, source_format, SOURCE, blocks)
    save_parent_child_chunks(session, chunks)
    return chunks


@pytest.mark.parametrize("source_format", ["txt", "md"])
def test_parents_children_and_global_metadata_survive_fresh_engine(engine, sessions, source_format):
    blocks, expected = prepare(source_format=source_format)
    with sessions.begin() as session:
        create_file(session, "file-1", f"notes.{source_format}")
        save_document_source(session, "file-1", source_format, SOURCE, blocks)
        save_parent_child_chunks(session, ParentChildChunks(
            parents=list(reversed(expected.parents)), children=list(reversed(expected.children)),
        ))
    engine.dispose()
    reopened = build_engine(str(engine.url))
    try:
        with build_session_factory(reopened)() as reader:
            parents = get_parents(reader, "file-1")
            children = get_chunks(reader, "file-1")
            assert parents == expected.parents
            assert children == expected.children
            assert all(type(child) is ChildChunk for child in children)
            assert get_document_source(reader, "file-1").blocks == blocks
            assert get_file(reader, "file-1").status == "processing"
        by_id = {parent.parent_id: parent for parent in parents}
        for child in children:
            parent = by_id[child.parent_id]
            assert parent.start_offset <= child.start_offset < child.end_offset <= parent.end_offset
            assert child.text == SOURCE[child.start_offset:child.end_offset]
            assert parent.text == SOURCE[parent.start_offset:parent.end_offset]
            assert child.heading_path == parent.heading_path
            assert set(child.source_block_indices) <= set(parent.source_block_indices)
            assert child.max_tokens == 16 and parent.max_tokens == 48
    finally:
        reopened.dispose()


def test_read_by_ids_handles_duplicates_missing_and_mixed_chunk_types(sessions):
    legacy = split_text("Legacy text.", "legacy")
    flat = split_structured(SOURCE, parse_markdown(SOURCE), "flat", max_tokens=32, encoding_name="cl100k_base")
    with sessions.begin() as session:
        hierarchy = store_document(session)
        for file_id in ("legacy", "flat"):
            create_file(session, file_id, f"{file_id}.txt")
        save_chunks(session, legacy + flat)
    with sessions() as reader:
        requested = [hierarchy.children[-1], legacy[0], flat[0]]
        loaded = get_chunks_by_ids(reader, [c.chunk_id for c in requested] + ["missing", legacy[0].chunk_id])
        assert {c.chunk_id: c for c in loaded} == {c.chunk_id: c for c in requested}
        assert {type(c) for c in loaded} == {Chunk, StructuredChunk, ChildChunk}
        selected = [hierarchy.parents[-1], hierarchy.parents[0]]
        loaded_parents = get_parents_by_ids(reader, [p.parent_id for p in selected] + ["missing", selected[0].parent_id])
        assert {p.parent_id: p for p in loaded_parents} == {p.parent_id: p for p in selected}
        assert get_parents(reader, "legacy") == get_parents(reader, "flat") == get_parents(reader, "missing") == []
        assert get_parents_by_ids(reader, []) == get_parents_by_ids(reader, ["missing"]) == []


def test_returned_parent_and_child_snapshots_do_not_mutate_stored_records(sessions):
    with sessions.begin() as session:
        expected = store_document(session)
    with sessions.begin() as session:
        parent = get_parents(session, "file-1")[0]
        child = get_chunks(session, "file-1")[0]
        parent.text = "Local change."
        parent.heading_path.clear()
        parent.source_block_indices.clear()
        child.parent_id = "Local change."
        child.heading_path.clear()
        child.source_block_indices.clear()
    with sessions() as reader:
        assert get_parents(reader, "file-1") == expected.parents
        assert get_chunks(reader, "file-1") == expected.children


def test_source_hierarchy_and_status_share_caller_owned_transaction(sessions):
    blocks, chunks = prepare()
    with sessions.begin() as session:
        create_file(session, "file-1", "notes.md")
    with sessions() as session:
        save_document_source(session, "file-1", "md", SOURCE, blocks)
        save_parent_child_chunks(session, chunks)
        update_file_status(session, "file-1", "ready")
        assert get_parents(session, "file-1") == chunks.parents
        assert get_chunks(session, "file-1") == chunks.children
        session.rollback()
    with sessions() as reader:
        assert get_document_source(reader, "file-1") is None
        assert get_parents(reader, "file-1") == get_chunks(reader, "file-1") == []
        assert reader.scalars(select(ChildParentRecord)).all() == []
        assert reader.scalars(select(ChunkStructureRecord)).all() == []
        assert get_file(reader, "file-1").status == "processing"


def test_missing_parent_rolls_back_source_parents_children_and_metadata(sessions):
    blocks, chunks = prepare()
    chunks.children[-1].parent_id = "missing"
    with sessions.begin() as session:
        create_file(session, "file-1", "notes.md")
    with pytest.raises(IntegrityError):
        with sessions.begin() as session:
            save_document_source(session, "file-1", "md", SOURCE, blocks)
            save_parent_child_chunks(session, chunks)
    with sessions() as reader:
        assert get_document_source(reader, "file-1") is None
        assert get_parents(reader, "file-1") == get_chunks(reader, "file-1") == []
        assert reader.scalars(select(ChildParentRecord)).all() == []
        assert reader.scalars(select(ChunkStructureRecord)).all() == []


@pytest.mark.parametrize("collision", ["parent_id", "file_index"])
def test_parent_identity_collisions_do_not_overwrite_existing_data(sessions, collision):
    with sessions.begin() as session:
        expected = store_document(session)
    duplicate = expected.parents[0].model_copy(update={"text": "Replacement."})
    if collision == "file_index":
        duplicate.parent_id = "new-id-same-index"
    with pytest.raises(IntegrityError):
        with sessions.begin() as session:
            save_parent_child_chunks(session, ParentChildChunks(parents=[duplicate], children=[]))
    with sessions() as reader:
        assert get_parents(reader, "file-1") == expected.parents
        assert get_chunks(reader, "file-1") == expected.children


def test_parent_requires_file_and_child_link_requires_structural_child(sessions):
    _, chunks = prepare()
    with pytest.raises(IntegrityError):
        with sessions.begin() as session:
            save_parent_child_chunks(session, ParentChildChunks(parents=chunks.parents, children=[]))
    with sessions.begin() as session:
        create_file(session, "file-1", "notes.md")
        save_parent_child_chunks(session, ParentChildChunks(parents=chunks.parents, children=[]))
    with pytest.raises(IntegrityError):
        with sessions.begin() as session:
            session.add(ChildParentRecord(chunk_id="missing", parent_id=chunks.parents[0].parent_id))
            session.flush()


def test_child_has_one_parent_and_referenced_parent_cannot_be_removed_alone(sessions):
    with sessions.begin() as session:
        expected = store_document(session)
    with pytest.raises(IntegrityError):
        with sessions.begin() as session:
            session.add(ChildParentRecord(
                chunk_id=expected.children[0].chunk_id, parent_id=expected.parents[-1].parent_id,
            ))
            session.flush()
    with pytest.raises(IntegrityError):
        with sessions.begin() as session:
            session.execute(delete(ParentChunkRecord).where(ParentChunkRecord.parent_id == expected.parents[0].parent_id))
    with sessions() as reader:
        assert get_chunks(reader, "file-1") == expected.children


@pytest.mark.parametrize("commit", [True, False])
def test_file_scoped_hierarchy_cleanup_is_transactional(sessions, commit):
    with sessions.begin() as session:
        removed = store_document(session)
        kept = store_document(session, "keep")
    with sessions() as session:
        delete_chunks(session, "file-1")
        delete_chunks(session, "file-1")
        assert get_parents(session, "file-1") == get_chunks(session, "file-1") == []
        assert get_document_source(session, "file-1") is not None
        delete_file_record(session, "file-1")
        if commit:
            session.commit()
        else:
            session.rollback()
    with sessions() as reader:
        assert get_parents(reader, "file-1") == ([] if commit else removed.parents)
        assert get_chunks(reader, "file-1") == ([] if commit else removed.children)
        assert (get_document_source(reader, "file-1") is None) == commit
        assert get_parents(reader, "keep") == kept.parents
        assert get_chunks(reader, "keep") == kept.children
        assert len(reader.scalars(select(ChildParentRecord)).all()) == len(kept.children) + (0 if commit else len(removed.children))


def test_childless_parents_cascade_with_file_deletion(sessions):
    _, chunks = prepare()
    with sessions.begin() as session:
        create_file(session, "file-1", "notes.md")
        save_parent_child_chunks(session, ParentChildChunks(parents=chunks.parents, children=[]))
    with sessions.begin() as session:
        delete_file_record(session, "file-1")
    with sessions() as reader:
        assert get_parents(reader, "file-1") == []


def test_init_db_adds_hierarchy_tables_without_rewriting_flat_schema(engine):
    new_tables = {"parent_chunks", "child_parents"}
    Base.metadata.create_all(engine, tables=[t for t in Base.metadata.sorted_tables if t.name not in new_tables])
    sessions = build_session_factory(engine)
    flat = split_structured(SOURCE, parse_markdown(SOURCE), "flat", max_tokens=32, encoding_name="cl100k_base")
    legacy = split_text("Legacy text.", "legacy")
    with sessions.begin() as session:
        for file_id in ("flat", "legacy"):
            create_file(session, file_id, "notes.txt")
        save_chunks(session, flat + legacy)
    old_columns = {name: inspect(engine).get_columns(name) for name in ("files", "chunks", "chunk_structures")}
    init_db(engine)
    init_db(engine)
    for name, columns in old_columns.items():
        assert [c["name"] for c in inspect(engine).get_columns(name)] == [c["name"] for c in columns]
    with sessions() as reader:
        assert get_chunks(reader, "flat") == flat
        assert get_chunks(reader, "legacy") == legacy
        assert get_parents(reader, "flat") == []
        assert reader.scalars(select(ChildParentRecord)).all() == []


def test_delete_service_removes_hierarchy_vectors_and_keeps_historical_evidence(storage):
    sessions, store, collection = storage
    with sessions.begin() as session:
        chunks = store_document(session)
        update_file_status(session, "file-1", "ready")
        store.upsert_chunks(chunks.children, [[1.0, 0.0] for _ in chunks.children])
        create_conversation(session, "conversation")
        child = chunks.children[0]
        answer = ChatAnswer(
            answer="Historical answer. [1]",
            sources=[AnswerSource(source_id=1, file_id="file-1", file_name="notes.md", chunk_id=child.chunk_id, text=child.text, distance=0.0)],
            citation_check=CitationCheck(valid_source_ids=[1], invalid_source_ids=[], no_citations=False),
        )
        message = save_message(session, "conversation", "assistant", answer.answer)
        save_answer_snapshot(session, message.message_id, "What does the guide say?", answer)
    delete_file("file-1", sessions, store)
    assert collection.count() == 0
    with sessions() as reader:
        assert get_parents(reader, "file-1") == get_chunks(reader, "file-1") == []
        assert get_document_source(reader, "file-1") is None
        assert reader.scalars(select(ChildParentRecord)).all() == []
        assert reader.scalars(select(ChunkStructureRecord)).all() == []
        assert reader.scalars(select(ChunkRecord)).all() == []
        saved = get_conversation_detail(reader, "conversation").messages[0].sources[0]
        assert saved.text == child.text and saved.file_deleted


def test_restart_cleanup_removes_abandoned_hierarchy_but_keeps_ready_data(storage):
    sessions, store, collection = storage
    with sessions.begin() as session:
        abandoned = store_document(session)
        kept = store_document(session, "keep")
        update_file_status(session, "keep", "ready")
        for chunks in (abandoned, kept):
            store.upsert_chunks(chunks.children, [[1.0, 0.0] for _ in chunks.children])
    recover_interrupted_files(sessions, store)
    with sessions() as reader:
        assert get_file(reader, "file-1").status == "failed"
        assert get_parents(reader, "file-1") == get_chunks(reader, "file-1") == []
        assert get_document_source(reader, "file-1").text == SOURCE
        assert get_parents(reader, "keep") == kept.parents
        assert get_chunks(reader, "keep") == kept.children
    assert set(collection.get()["ids"]) == {c.chunk_id for c in kept.children}
