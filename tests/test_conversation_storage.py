"""Conversation and message persistence using real SQLite transactions."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from knowledgebase.schemas import ConversationInfo, MessageInfo
from knowledgebase.storage.database import build_engine, build_session_factory, init_db
from knowledgebase.storage.models import ChunkRecord, FileRecord, MessageRecord
from knowledgebase.storage.operations import (
    create_conversation,
    get_conversation,
    get_file,
    get_messages,
    save_message,
)


@pytest.fixture
def sessions(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'conversations.db'}")
    init_db(engine)
    try:
        yield build_session_factory(engine)
    finally:
        engine.dispose()


def test_conversation_and_messages_round_trip_as_detached_snapshots(sessions):
    before = datetime.now(UTC).replace(tzinfo=None)
    text = "  The café closes at 5 PM. 🙂\r\n"
    with sessions.begin() as session:
        assert create_conversation(session, "chat-1") is None
        user = save_message(session, "chat-1", "user", "When does it close?")
        assistant = save_message(session, "chat-1", "assistant", text)
        assert isinstance(user, MessageInfo)
        assert assistant.message_id > user.message_id

    with sessions() as session:
        conversation = get_conversation(session, "chat-1")
        messages = get_messages(session, "chat-1")
    assert isinstance(conversation, ConversationInfo)
    assert conversation.conversation_id == "chat-1"
    assert messages == [user, assistant]
    assert messages[1].content == text
    for timestamp in [conversation.created_at, user.created_at, assistant.created_at]:
        assert timestamp.tzinfo is None
        assert before <= timestamp <= datetime.now(UTC).replace(tzinfo=None)
    conversation.conversation_id = "local-change"
    messages[1].content = "Local change."
    with sessions() as reader:
        assert get_conversation(reader, "chat-1").conversation_id == "chat-1"
        assert get_messages(reader, "chat-1")[1].content == text


@pytest.mark.parametrize("limit, expected_positions", [(None, [0, 1, 2, 3]), (2, [2, 3]), (1, [3]), (10, [0, 1, 2, 3])])
def test_recent_messages_preserve_append_order_and_conversation_isolation(sessions, limit, expected_positions):
    tied = datetime(2026, 1, 1)
    expected = []
    with sessions.begin() as session:
        create_conversation(session, "chat-1")
        create_conversation(session, "chat-2")
        for i in range(4):
            message = save_message(session, "chat-1", "user" if i % 2 == 0 else "assistant", f"Message {i}")
            session.get(MessageRecord, message.message_id).created_at = tied
            expected.append(message.message_id)
            save_message(session, "chat-2", "user", "Other conversation.")

    with sessions() as session:
        messages = get_messages(session, "chat-1", limit=limit)
    assert [m.message_id for m in messages] == [expected[i] for i in expected_positions]
    assert all(m.conversation_id == "chat-1" and m.created_at == tied for m in messages)


def test_empty_and_unknown_conversations(sessions):
    with sessions.begin() as session:
        create_conversation(session, "empty")
    with sessions() as session:
        assert get_conversation(session, "empty") is not None
        assert get_conversation(session, "missing") is None
        assert get_messages(session, "empty") == []
        assert get_messages(session, "missing", limit=5) == []


@pytest.mark.parametrize("limit", [0, -1])
def test_invalid_history_limit_is_rejected(sessions, limit):
    with sessions() as session:
        with pytest.raises(ValueError, match="positive"):
            get_messages(session, "chat-1", limit=limit)


def test_storage_helpers_and_reads_leave_commit_to_caller(sessions):
    with sessions() as session:
        create_conversation(session, "chat-1")
        save_message(session, "chat-1", "user", "Question?")
        assert get_conversation(session, "chat-1") is not None
        assert len(get_messages(session, "chat-1")) == 1
        session.rollback()
    with sessions() as reader:
        assert get_conversation(reader, "chat-1") is None
        assert get_messages(reader, "chat-1") == []


def test_question_and_answer_can_be_saved_atomically(sessions):
    with sessions.begin() as session:
        create_conversation(session, "chat-1")
        save_message(session, "chat-1", "user", "Keep this earlier message.")
    with pytest.raises(RuntimeError, match="Exchange failed"):
        with sessions.begin() as session:
            save_message(session, "chat-1", "user", "New question?")
            save_message(session, "chat-1", "assistant", "New answer.")
            raise RuntimeError("Exchange failed")
    with sessions() as reader:
        assert [m.content for m in get_messages(reader, "chat-1")] == ["Keep this earlier message."]


@pytest.mark.parametrize("conversation_id, role", [("missing", "user"), ("chat-1", "system")])
def test_database_rejects_missing_conversation_and_invalid_role(sessions, conversation_id, role):
    with sessions.begin() as session:
        create_conversation(session, "chat-1")
    with pytest.raises(IntegrityError):
        with sessions.begin() as session:
            save_message(session, conversation_id, role, "Content.")
    with sessions() as reader:
        assert get_messages(reader, "chat-1") == []


def test_duplicate_conversation_does_not_replace_history(sessions):
    with sessions.begin() as session:
        create_conversation(session, "chat-1")
        save_message(session, "chat-1", "user", "Original.")
    with pytest.raises(IntegrityError):
        with sessions.begin() as session:
            create_conversation(session, "chat-1")
    with sessions() as reader:
        assert [m.content for m in get_messages(reader, "chat-1")] == ["Original."]


def test_init_db_adds_conversation_tables_to_existing_file_database(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'existing.db'}")
    try:
        FileRecord.__table__.create(engine)
        ChunkRecord.__table__.create(engine)
        sessions = build_session_factory(engine)
        with sessions.begin() as session:
            session.add(FileRecord(file_id="keep", file_name="notes.txt"))
        init_db(engine)
        with sessions.begin() as session:
            create_conversation(session, "chat-1")
            save_message(session, "chat-1", "user", "Persist across connections.")
        engine.dispose()
        init_db(engine)
        with sessions() as reader:
            assert get_file(reader, "keep").file_name == "notes.txt"
            assert get_messages(reader, "chat-1")[0].content == "Persist across connections."
        assert set(inspect(engine).get_table_names()) == {"files", "chunks", "conversations", "messages", "answer_snapshots"}
    finally:
        engine.dispose()
