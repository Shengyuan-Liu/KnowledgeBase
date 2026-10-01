"""Check incremental HTTP delivery, cancellation, and atomic stream persistence."""

import json
from unittest.mock import Mock

import anyio
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import func, select

from knowledgebase.api import app as api_module
from knowledgebase.providers.llm import LLMClient
from knowledgebase.rag.generation import INSUFFICIENT_EVIDENCE
from knowledgebase.storage.models import AnswerSnapshotRecord, ConversationRecord, MessageRecord
from knowledgebase.storage.operations import get_conversation_detail
from knowledgebase.services.files import FileService


class TextStream:
    def __init__(self):
        self.deltas = ["The café ", "closes at 5 PM. [1]\n"]
        self.failure = False
        self.gate = None
        self.closed = False
        self.messages = None

    async def stream(self, messages):
        self.messages = messages
        try:
            for delta in self.deltas:
                yield delta
            if self.gate is not None:
                await self.gate.wait()
            if self.failure:
                raise RuntimeError("Private provider diagnostic.")
        finally:
            self.closed = True


@pytest.fixture
def streaming_app(configured_app, monkeypatch):
    app, _, _ = configured_app
    llm = Mock(spec=LLMClient)
    llm.generate.return_value = "When does the café close?"
    streamer = TextStream()
    monkeypatch.setattr(api_module, "LLMClient", Mock(return_value=llm))
    monkeypatch.setattr(api_module, "StreamingLLMClient", Mock(return_value=streamer))
    return app, streamer


def ingest(resources):
    return FileService(resources.sessions, resources.store, embeddings=resources.embeddings).ingest("hours.txt", "The café closes at 5 PM.".encode())


def frames(text):
    result = []
    for frame in text.split("\n\n"):
        if frame:
            event, data = frame.split("\n")
            result.append((event.removeprefix("event: "), json.loads(data.removeprefix("data: "))))
    return result


def assert_no_turn(resources):
    with resources.sessions() as session:
        for record in (ConversationRecord, MessageRecord, AnswerSnapshotRecord):
            assert session.scalar(select(func.count()).select_from(record)) == 0


def test_stream_sources_deltas_complete_and_followup_match_saved_history(streaming_app):
    app, streamer = streaming_app
    with TestClient(app) as client:
        resources = app.state.resources
        file_id = ingest(resources)
        response = client.post("/api/chat/stream", json={"question": "  Hours?\n", "request_id": "one"})
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert response.headers["cache-control"] == "no-cache"
        events = frames(response.text)
        assert [kind for kind, _ in events] == ["start", "sources", "answer_delta", "answer_delta", "debug", "complete"]
        assert all(data["request_id"] == "one" for _, data in events)
        assert events[0][1]["conversation_id"] is None
        assert all("message_id" not in data for _, data in events[:-1])
        complete = events[-1][1]
        assert complete["answer"] == "".join(streamer.deltas)
        assert complete["question"] == "  Hours?\n"
        assert complete["sources"] == events[1][1]["sources"]
        assert complete["sources"][0]["file_id"] == file_id
        assert complete["citation_check"]["valid_source_ids"] == [1]
        assert events[-2][1]["distance_metric"] == "cosine"
        saved = client.get(f"/api/conversations/{complete['conversation_id']}").json()["messages"][-1]
        assert saved["message_id"] == complete["message_id"]
        assert saved["content"] == complete["answer"]
        assert saved["sources"] == [{**s, "file_deleted": False} for s in complete["sources"]]
        assert saved["citation_check"] == complete["citation_check"]
        assert streamer.closed
        assert '"file_name": "hours.txt"' in streamer.messages[0]["content"]
        assert "Excerpt:\nThe café closes at 5 PM." in streamer.messages[0]["content"]
        assert complete['retrieval']['context_format'] == 'source-metadata-v1'
        assert saved['retrieval']['context_format'] == 'source-metadata-v1'

        followup = client.post("/api/chat/stream", json={
            "question": "What time?", "request_id": "two", "conversation_id": complete["conversation_id"],
        })
        second = frames(followup.text)[-1][1]
        assert second["conversation_id"] == complete["conversation_id"]
        assert second["retrieval_question"] == "When does the café close?"
        assert "Question:\nWhat time?" in streamer.messages[0]["content"]
        assert "Conversation interpretation (not evidence):\nWhen does the café close?" in streamer.messages[0]["content"]
        resources.embeddings.embed_query.assert_called_with(second["retrieval_question"])
        assert len(client.get(f"/api/conversations/{complete['conversation_id']}").json()["messages"]) == 4


def test_stream_empty_library_and_pre_stream_http_errors(streaming_app):
    app, streamer = streaming_app
    with TestClient(app) as client:
        for payload in ({"question": "", "request_id": "one"}, {"question": "Hours?"},
                        {"question": "Hours?", "request_id": "  "}):
            assert client.post("/api/chat/stream", json=payload).status_code == 422
        missing = client.post("/api/chat/stream", json={
            "question": "Hours?", "request_id": "one", "conversation_id": "missing",
        })
        assert missing.status_code == 404
        assert missing.headers["content-type"] == "application/json"
        response = client.post("/api/chat/stream", json={"question": "Hours?", "request_id": "empty"})
        complete = frames(response.text)[-1][1]
        assert complete["answer"] == INSUFFICIENT_EVIDENCE
        assert complete["sources"] == []
        assert streamer.messages is None
        app.state.resources.llm.generate.assert_not_called()
        app.state.resources.embeddings.embed_query.assert_not_called()
        schema = client.get("/openapi.json").json()
        assert "text/event-stream" in schema["paths"]["/api/chat/stream"]["post"]["responses"]["200"]["content"]


@pytest.mark.parametrize("stage", ["generation", "retrieval", "saving"])
def test_stream_failure_emits_error_without_complete_or_partial_records(streaming_app, monkeypatch, stage):
    from knowledgebase.services import chat

    app, streamer = streaming_app
    with TestClient(app) as client:
        resources = app.state.resources
        ingest(resources)
        if stage == "generation":
            streamer.failure = True
        elif stage == "retrieval":
            resources.embeddings.embed_query.side_effect = RuntimeError("Private error.")
        else:
            save_snapshot = chat.save_answer_snapshot

            def fail_snapshot(*args):
                save_snapshot(*args)
                raise RuntimeError("Private error.")

            monkeypatch.setattr(chat, "save_answer_snapshot", fail_snapshot)
        response = client.post("/api/chat/stream", json={"question": "Hours?", "request_id": "failure"})
        assert response.status_code == 200
        events = frames(response.text)
        assert events[-1] == ("error", {"request_id": "failure", "message": "Answer processing failed."})
        assert "complete" not in [kind for kind, _ in events]
        assert_no_turn(resources)


async def asgi_stream(app, send, disconnect):
    received_body = False

    async def receive():
        nonlocal received_body
        if not received_body:
            received_body = True
            return {"type": "http.request", "body": b'{"question":"Hours?","request_id":"live"}', "more_body": False}
        await disconnect.wait()
        return {"type": "http.disconnect"}

    scope = {"type": "http", "asgi": {"version": "3.0", "spec_version": "2.4"},
             "http_version": "1.1", "method": "POST", "scheme": "http",
             "path": "/api/chat/stream", "raw_path": b"/api/chat/stream", "query_string": b"",
             "headers": [(b"content-type", b"application/json")], "server": ("test", 80), "client": ("test", 1)}
    await app(scope, receive, send)


@pytest.mark.anyio
@pytest.mark.parametrize("ending", ["complete", "disconnect", "send_error"])
async def test_http_delivers_deltas_before_model_finishes_and_cancels_on_disconnect(streaming_app, ending):
    app, streamer = streaming_app
    streamer.gate = anyio.Event()
    seen_delta, disconnect, finished = anyio.Event(), anyio.Event(), anyio.Event()
    messages = []

    async def send(message):
        messages.append(message)
        if b"event: answer_delta" in message.get("body", b""):
            seen_delta.set()
            if ending == "send_error":
                raise OSError("Socket closed.")

    async def request():
        try:
            await asgi_stream(app, send, disconnect)
        finally:
            finished.set()

    async with app.router.lifespan_context(app):
        resources = app.state.resources
        ingest(resources)
        with anyio.fail_after(5):
            async with anyio.create_task_group() as tasks:
                tasks.start_soon(request)
                await seen_delta.wait()
                assert_no_turn(resources)
                if ending != "send_error":
                    assert not finished.is_set()
                    assert not streamer.closed
                    if ending == "disconnect":
                        disconnect.set()
                    else:
                        streamer.gate.set()
                await finished.wait()
        events = frames(b"".join(m.get("body", b"") for m in messages).decode())
        assert streamer.closed
        if ending != "complete":
            assert "complete" not in [kind for kind, _ in events]
            assert_no_turn(resources)
        else:
            assert events[-1][0] == "complete"
            with resources.sessions() as session:
                detail = get_conversation_detail(session, events[-1][1]["conversation_id"])
            assert detail.messages[-1].content == "".join(streamer.deltas)


def test_failed_followup_keeps_existing_exchange_and_does_not_start_answer_stream(streaming_app):
    app, streamer = streaming_app
    with TestClient(app) as client:
        resources = app.state.resources
        ingest(resources)
        response = client.post("/api/chat/stream", json={"question": "Hours?", "request_id": "first"})
        first = frames(response.text)[-1][1]
        path = f"/api/conversations/{first['conversation_id']}"
        history = client.get(path).json()
        resources.llm.generate.side_effect = RuntimeError("Resolution failed.")
        streamer.messages = None
        failed = client.post("/api/chat/stream", json={
            "question": "What time?", "request_id": "second", "conversation_id": first["conversation_id"],
        })
        assert [kind for kind, _ in frames(failed.text)] == ["start", "error"]
        assert client.get(path).json() == history
        assert streamer.messages is None


def test_internal_lookup_failure_during_stream_setup_is_500(streaming_app, monkeypatch):
    from knowledgebase.services import chat

    app, _ = streaming_app
    monkeypatch.setattr(chat, "get_conversation", Mock(side_effect=KeyError("Internal lookup failed.")))
    with TestClient(app) as client:
        response = client.post("/api/chat/stream", json={
            "question": "Hours?", "request_id": "failure", "conversation_id": "one",
        })
        assert response.status_code == 500
        assert response.json() == {"detail": "Stream setup failed."}


@pytest.mark.anyio
async def test_disconnect_during_rerank_does_not_generate_or_save(streaming_app):
    """An abandoned scoring request can finish without continuing the answer."""
    from threading import Event
    from knowledgebase.schemas import RelevanceScore

    app, streamer = streaming_app
    started, disconnect, finished = anyio.Event(), anyio.Event(), anyio.Event()
    release, scored = Event(), Event()
    messages = []

    def score(question, candidates):
        anyio.from_thread.run_sync(started.set)
        try:
            assert release.wait(5)
            return [RelevanceScore(chunk_id=c.chunk_id, score=3.25) for c in candidates]
        finally:
            scored.set()

    async def send(message):
        messages.append(message)

    async def request():
        try:
            await asgi_stream(app, send, disconnect)
        finally:
            finished.set()

    async with app.router.lifespan_context(app):
        resources = app.state.resources
        resources.settings.rerank_enabled = True
        resources.reranker = Mock(model="offline-reranker", model_revision="test-revision", device="cpu", max_pair_tokens=1024, batch_size=4, score=Mock(side_effect=score))
        ingest(resources)
        try:
            with anyio.fail_after(5):
                async with anyio.create_task_group() as tasks:
                    tasks.start_soon(request)
                    await started.wait()
                    disconnect.set()
                    await finished.wait()
                    assert not scored.is_set()
        finally:
            release.set()
            assert await anyio.to_thread.run_sync(scored.wait, 5)
        assert streamer.messages is None
        events = frames(b"".join(m.get("body", b"") for m in messages).decode())
        assert [kind for kind, _ in events] == ["start"]
        assert_no_turn(resources)
