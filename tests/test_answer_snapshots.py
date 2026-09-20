"""Persist answer evidence without tying historical excerpts to live files."""

import pytest
from sqlalchemy import inspect

from knowledgebase.schemas import AnswerSource, ChatAnswer, CitationCheck
from knowledgebase.storage.database import build_engine, build_session_factory, init_db
from knowledgebase.storage.models import Base, FileRecord
from knowledgebase.storage.operations import (
    create_conversation, get_conversation_detail, get_messages,
    save_answer_snapshot, save_message,
)


@pytest.fixture
def sessions(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'snapshots.db'}")
    init_db(engine)
    try:
        yield build_session_factory(engine)
    finally:
        engine.dispose()


def make_answer(text="  The café closes at 5 PM. 🙂\r\n"):
    return ChatAnswer(
        answer="5 PM. [1] Invalid reference. [7]",
        sources=[AnswerSource(
            source_id=1, file_id="hours", file_name="hours.txt", chunk_id="hours:0",
            text=text, distance=0.125,
        )],
        citation_check=CitationCheck(valid_source_ids=[1], invalid_source_ids=[7], no_citations=False),
    )


def test_snapshots_preserve_order_message_association_and_detached_values(sessions):
    first, second = make_answer(), make_answer("Second answer's evidence.")
    with sessions.begin() as session:
        session.add(FileRecord(file_id="hours", file_name="hours.txt", status="ready"))
        create_conversation(session, "one")
        create_conversation(session, "two")
        for answer in (first, second):
            save_message(session, "one", "user", "What time?")
            message = save_message(session, "one", "assistant", answer.answer)
            save_answer_snapshot(session, message.message_id, "When does the café close?", answer)
        save_message(session, "two", "user", "Other conversation.")
    with sessions() as session:
        detail = get_conversation_detail(session, "one")
        assert len(get_conversation_detail(session, "two").messages) == 1
        # Reference-resolution history still contains only message text and identity.
        assert "sources" not in get_messages(session, "one")[1].model_dump()
    assert [message.role for message in detail.messages] == ["user", "assistant", "user", "assistant"]
    assert [message.message_id for message in detail.messages] == sorted(message.message_id for message in detail.messages)
    for position, answer in ((1, first), (3, second)):
        saved = detail.messages[position]
        assert saved.content == answer.answer
        assert saved.retrieval_question == "When does the café close?"
        assert saved.citation_check == answer.citation_check
        assert saved.sources[0].model_dump() == {**answer.sources[0].model_dump(), "file_deleted": False}
    assert detail.messages[0].sources is None
    detail.messages[1].sources[0].text = "Local mutation."
    detail.messages[1].citation_check.valid_source_ids.clear()
    with sessions() as session:
        saved = get_conversation_detail(session, "one").messages[1]
        assert saved.sources[0].text == first.sources[0].text
        assert saved.citation_check == first.citation_check


def test_snapshot_write_leaves_commit_to_caller(sessions):
    with sessions.begin() as session:
        create_conversation(session, "one")
        message = save_message(session, "one", "assistant", "Earlier message.")
    with sessions() as session:
        save_answer_snapshot(session, message.message_id, "Hours?", make_answer())
        assert get_conversation_detail(session, "one").messages[0].sources is not None
        session.rollback()
    with sessions() as session:
        assert get_conversation_detail(session, "one").messages[0].sources is None


def test_init_db_adds_snapshots_to_old_database_without_rewriting_history(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    try:
        Base.metadata.create_all(engine, tables=[
            table for table in Base.metadata.sorted_tables if table.name != "answer_snapshots"
        ])
        sessions = build_session_factory(engine)
        with sessions.begin() as session:
            create_conversation(session, "legacy")
            save_message(session, "legacy", "user", "Old question?")
            save_message(session, "legacy", "assistant", "Old answer. [1]")
        init_db(engine)
        engine.dispose()
        init_db(engine)
        assert "answer_snapshots" in inspect(engine).get_table_names()
        with sessions() as session:
            detail = get_conversation_detail(session, "legacy")
        assert [m.content for m in detail.messages] == ["Old question?", "Old answer. [1]"]
        assert all(m.sources is None and m.retrieval_question is None and m.citation_check is None
                   for m in detail.messages)
    finally:
        engine.dispose()
