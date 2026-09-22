"""HTTP chat with real SQLite/Chroma and offline provider responses."""

import json
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import func, select

from knowledgebase.api import app as api_module
from knowledgebase.rag.generation import INSUFFICIENT_EVIDENCE
from knowledgebase.storage.models import AnswerSnapshotRecord, ConversationRecord, MessageRecord
from knowledgebase.storage.operations import create_conversation, get_messages, save_message


@pytest.fixture
def api(configured_app):
    app, _, sdk = configured_app
    with TestClient(app) as client:
        yield client, app.state.resources, sdk.responses.create
    sdk.__exit__.assert_called_once()


def upload(client):
    response = client.post("/api/files", files={
        "file": ("hours.txt", b"The library closes at 5 PM.", "text/plain"),
    })
    assert response.status_code == 201
    return response.json()["file_id"]


def test_upload_question_followup_and_persisted_exchange(api):
    client, resources, generate = api
    file_id = upload(client)
    generate.side_effect = [SimpleNamespace(output_text=text) for text in (
        "The library closes at 5 PM. [1]",
        "When does the library close?",
        "At 5 PM. [1]",
    )]
    question = "  When does the library close?\n"
    response = client.post("/api/chat", json={"question": question})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    first = response.json()
    assert first["question"] == first["retrieval_question"] == question
    assert first["answer"] == "The library closes at 5 PM. [1]"
    assert first["sources"] == [{
        "source_id": 1, "file_id": file_id, "file_name": "hours.txt",
        "chunk_id": f"{file_id}:structural:0", "text": "The library closes at 5 PM.",
        "distance": pytest.approx(0.0),
    }]
    assert first["citation_check"] == {
        "valid_source_ids": [1], "invalid_source_ids": [], "no_citations": False,
    }

    response = client.post("/api/chat", json={
        "question": "What time was that?", "conversation_id": first["conversation_id"],
    })
    assert response.status_code == 200
    second = response.json()
    assert second["conversation_id"] == first["conversation_id"]
    assert second["message_id"] > first["message_id"]
    assert second["answer"] == "At 5 PM. [1]"
    assert second["retrieval_question"] == "When does the library close?"
    resources.embeddings.embed_query.assert_called_with(second["retrieval_question"])
    history = json.loads(generate.call_args_list[1].kwargs["input"][1]["content"])["history"]
    assert history == [{"role": "user", "content": question},
                       {"role": "assistant", "content": first["answer"]}]
    assert all(call.kwargs["model"] == "gpt-4.1" for call in generate.call_args_list)
    with resources.sessions() as session:
        messages = get_messages(session, first["conversation_id"])
    assert [(m.role, m.content) for m in messages] == [
        ("user", question), ("assistant", first["answer"]),
        ("user", second["question"]), ("assistant", second["answer"]),
    ]
    assert messages[-1].message_id == second["message_id"]


@pytest.mark.parametrize("payload", [
    {}, {"question": ""}, {"question": " \n\t"},
    {"question": None}, {"question": 42},
])
def test_invalid_question_is_422_without_calls_or_records(api, payload):
    client, resources, generate = api
    assert client.post("/api/chat", json=payload).status_code == 422
    generate.assert_not_called()
    resources.embeddings.embed_query.assert_not_called()
    with resources.sessions() as session:
        assert session.scalar(select(func.count()).select_from(ConversationRecord)) == 0
        assert session.scalar(select(func.count()).select_from(MessageRecord)) == 0


def test_unknown_conversation_is_404_without_model_calls(api):
    client, resources, generate = api
    response = client.post("/api/chat", json={"question": "Hours?", "conversation_id": "missing"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Conversation not found."}
    generate.assert_not_called()
    resources.embeddings.embed_query.assert_not_called()
    with resources.sessions() as session:
        assert get_messages(session, "missing") == []


def test_empty_library_returns_saved_insufficient_evidence_answer(api):
    client, resources, generate = api
    response = client.post("/api/chat", json={"question": "Hours?", "conversation_id": None})
    assert response.status_code == 200
    result = response.json()
    assert result["answer"] == INSUFFICIENT_EVIDENCE
    assert result["sources"] == []
    assert result["citation_check"] == {
        "valid_source_ids": [], "invalid_source_ids": [], "no_citations": True,
    }
    generate.assert_not_called()
    resources.embeddings.embed_query.assert_not_called()
    with resources.sessions() as session:
        assert [m.content for m in get_messages(session, result["conversation_id"])] == [
            "Hours?", INSUFFICIENT_EVIDENCE,
        ]


@pytest.mark.parametrize("error_type", [ValueError, KeyError, IndexError])
def test_failed_first_answer_is_500_without_new_conversation(api, error_type):
    client, resources, generate = api
    upload(client)
    generate.side_effect = error_type("Private provider diagnostics.")
    response = client.post("/api/chat", json={"question": "Hours?"})
    assert response.status_code == 500
    assert response.json() == {"detail": "Answer processing failed."}
    with resources.sessions() as session:
        assert session.scalar(select(func.count()).select_from(ConversationRecord)) == 0
        assert session.scalar(select(func.count()).select_from(MessageRecord)) == 0


@pytest.mark.parametrize("stage", ["resolution", "retrieval", "generation", "saving", "snapshot"])
def test_failed_followup_is_500_without_partial_exchange(api, monkeypatch, stage):
    from knowledgebase.services import chat

    client, resources, generate = api
    upload(client)
    generate.return_value = SimpleNamespace(output_text="At 5 PM. [1]")
    first = client.post("/api/chat", json={"question": "Hours?"}).json()
    failure = RuntimeError("Private failure details.")
    resolved = SimpleNamespace(output_text="When does the library close?")
    if stage == "resolution":
        generate.side_effect = failure
    elif stage == "retrieval":
        generate.return_value = resolved
        resources.embeddings.embed_query.side_effect = failure
    elif stage == "generation":
        generate.side_effect = [resolved, failure]
    elif stage == "saving":
        save_message = chat.save_message

        def fail_assistant(session, conversation_id, role, content):
            if role == "assistant":
                raise failure
            return save_message(session, conversation_id, role, content)

        monkeypatch.setattr(chat, "save_message", fail_assistant)
    else:
        save_snapshot = chat.save_answer_snapshot

        def fail_snapshot(*args):
            save_snapshot(*args)
            raise failure

        monkeypatch.setattr(chat, "save_answer_snapshot", fail_snapshot)
    response = client.post("/api/chat", json={
        "question": "What time?", "conversation_id": first["conversation_id"],
    })
    assert response.status_code == 500
    assert response.json() == {"detail": "Answer processing failed."}
    with resources.sessions() as session:
        assert [m.content for m in get_messages(session, first["conversation_id"])] == [
            "Hours?", first["answer"],
        ]
        assert session.scalar(select(func.count()).select_from(AnswerSnapshotRecord)) == 1


def test_openapi_describes_json_request_response_and_errors(api):
    client, _, _ = api
    schema = client.get("/openapi.json").json()
    endpoint = schema["paths"]["/api/chat"]["post"]
    assert endpoint["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("/ChatRequest")
    assert endpoint["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("/ConversationAnswer")
    assert {"404", "422", "500"} <= endpoint["responses"].keys()
    read = schema["paths"]["/api/conversations/{conversation_id}"]["get"]
    assert read["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("/ConversationDetail")
    assert "404" in read["responses"]


def test_read_conversation_after_restart_restores_answer_and_sources(configured_app):
    app, embeddings, sdk = configured_app
    sdk.responses.create.return_value = SimpleNamespace(output_text="At 5 PM. [1] Missing. [7]")
    with TestClient(app) as client:
        upload(client)
        answer = client.post("/api/chat", json={"question": "  Hours?\n"}).json()
        path = f"/api/conversations/{answer['conversation_id']}"
        before = client.get(path)
        assert before.status_code == 200
    sdk.responses.create.reset_mock()
    embeddings.reset_mock()
    with TestClient(api_module.create_app()) as client:
        after = client.get(path)
    assert after.status_code == 200
    assert after.json() == before.json()
    detail = after.json()
    assert detail["conversation_id"] == answer["conversation_id"]
    assert detail["created_at"]
    assert [m["content"] for m in detail["messages"]] == [answer["question"], answer["answer"]]
    saved = detail["messages"][1]
    assert saved["message_id"] == answer["message_id"]
    assert saved["retrieval_question"] == answer["retrieval_question"]
    assert saved["citation_check"] == answer["citation_check"]
    assert saved["sources"] == [{**source, "file_deleted": False} for source in answer["sources"]]
    sdk.responses.create.assert_not_called()
    embeddings.embed_query.assert_not_called()
    embeddings.embed_documents.assert_not_called()
    assert sdk.__exit__.call_count == 2


def test_read_unknown_empty_and_legacy_conversations_without_model_calls(api):
    client, resources, generate = api
    with resources.sessions.begin() as session:
        create_conversation(session, "empty")
        create_conversation(session, "legacy")
        save_message(session, "legacy", "user", "Question?")
        save_message(session, "legacy", "assistant", "Legacy answer. [1]")
    missing = client.get("/api/conversations/missing")
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Conversation not found."}
    assert client.get("/api/conversations/empty").json()["messages"] == []
    legacy = client.get("/api/conversations/legacy").json()["messages"]
    assert [m["content"] for m in legacy] == ["Question?", "Legacy answer. [1]"]
    assert all(m["sources"] is None and m["citation_check"] is None and m["retrieval_question"] is None
               for m in legacy)
    generate.assert_not_called()
    resources.embeddings.embed_query.assert_not_called()


def test_deleted_source_remains_historical_but_cannot_answer_followup(api):
    client, resources, generate = api
    file_id = upload(client)
    generate.return_value = SimpleNamespace(output_text="At 5 PM. [1]")
    first = client.post("/api/chat", json={"question": "Hours?"}).json()
    assert client.delete(f"/api/files/{file_id}").status_code == 204
    generate.reset_mock()
    resources.embeddings.reset_mock()
    generate.return_value = SimpleNamespace(output_text="When does the library close?")
    response = client.post("/api/chat", json={
        "question": "What time was that?", "conversation_id": first["conversation_id"],
    })
    assert response.status_code == 200
    followup = response.json()
    assert followup["answer"] == INSUFFICIENT_EVIDENCE
    assert followup["sources"] == []
    generate.assert_called_once()  # Reference resolution only.
    resources.embeddings.embed_query.assert_not_called()
    saved = client.get(f"/api/conversations/{first['conversation_id']}").json()["messages"]
    assert saved[1]["sources"] == [{**source, "file_deleted": True} for source in first["sources"]]
    assert saved[1]["citation_check"] == first["citation_check"]
    assert saved[3]["sources"] == []  # Recorded empty retrieval, distinct from legacy null.
    assert saved[3]["citation_check"] == followup["citation_check"]
    assert saved[3]["retrieval_question"] == followup["retrieval_question"]


def test_snapshot_failure_rolls_back_new_conversation_and_messages(api, monkeypatch):
    from knowledgebase.services import chat

    client, resources, _ = api
    save_snapshot = chat.save_answer_snapshot

    def fail_snapshot(*args):
        save_snapshot(*args)
        raise RuntimeError("Snapshot transaction failed.")

    monkeypatch.setattr(chat, "save_answer_snapshot", fail_snapshot)
    response = client.post("/api/chat", json={"question": "Hours?"})
    assert response.status_code == 500
    with resources.sessions() as session:
        for record in (ConversationRecord, MessageRecord, AnswerSnapshotRecord):
            assert session.scalar(select(func.count()).select_from(record)) == 0
