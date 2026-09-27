"""Bounded planner and real chat/storage integration with offline provider responses."""

from contextlib import aclosing
import json
from threading import Event
from types import SimpleNamespace
from unittest.mock import Mock

import anyio
from fastapi.testclient import TestClient
import httpx2
from openai import OpenAI
import pytest
from sqlalchemy import func, select

from knowledgebase.config import PlanningOptions, Settings
from knowledgebase.providers.planner import PlannerClient
from knowledgebase.rag.planning import PlanDecision
from knowledgebase.services.chat import stream_answer_in_conversation
from knowledgebase.services.planning import NARROWING_MESSAGE
from knowledgebase.storage.models import MessageRecord

DIRECT = {"route": "direct", "requirements": [], "queries": [], "dependencies": []}
DECOMPOSED = {
    "route": "decomposed", "dependencies": [],
    "requirements": [{"requirement_id": "method", "description": "Training method"},
                     {"requirement_id": "result", "description": "Evaluation result"}],
    "queries": [{"query_id": "method", "text": "training method", "requirement_ids": ["method"]},
                {"query_id": "result", "text": "evaluation result", "requirement_ids": ["result"]}],
}


def response(text, *, status="completed"):
    return SimpleNamespace(output_text=text, status=status, model="resolved-planner-model", id="resp_offline",
                           usage=SimpleNamespace(model_dump=lambda **_: {"input_tokens": 33, "output_tokens": 44, "total_tokens": 77}))


def sdk_response(text):
    return {"id": "resp_offline", "object": "response", "created_at": 0, "status": "completed", "model": "resolved-planner-model",
            "output": [{"id": "msg_offline", "type": "message", "role": "assistant", "status": "completed",
                        "content": [{"type": "output_text", "text": text, "annotations": []}]}],
            "usage": {"input_tokens": 33, "output_tokens": 44, "total_tokens": 77,
                      "input_tokens_details": {"cached_tokens": 0}, "output_tokens_details": {"reasoning_tokens": 0}}}


def test_real_sdk_planning_schema_limits_identity_and_usage():
    requests = []
    def handle(request):
        payload = json.loads(request.content)
        requests.append(payload)
        assert payload["max_output_tokens"] == 2048
        assert payload["text"]["format"]["strict"] is True
        schema = payload["text"]["format"]["schema"]
        assert set(schema["required"]) == set(schema["properties"])
        assert "original_question" not in schema["properties"]
        assert "file_ids" not in schema["$defs"]["DraftQuery"]["properties"]
        return httpx2.Response(200, json=sdk_response(json.dumps(DECOMPOSED)))
    with OpenAI(api_key="offline", base_url="https://offline.test/v1",
                http_client=httpx2.Client(transport=httpx2.MockTransport(handle))) as sdk:
        planner = PlannerClient(sdk, "requested-model", PlanningOptions(), "cl100k_base")
        result = planner.plan("What about it?", "Explain training and results.", lambda: 10)
    assert len(requests) == 1
    assert result.plan.original_question == "What about it?"
    assert result.plan.resolved_question == "Explain training and results."
    assert all(query.file_ids is None for query in result.plan.queries)
    assert result.record["timeout_seconds"] == 10
    assert result.record["model"] == "resolved-planner-model"
    assert result.record["usage"]["total_tokens"] == 77
    assert result.record["billed_cost"] is None


@pytest.mark.parametrize("output,status", [
    ("not JSON", "completed"), (json.dumps(DIRECT), "incomplete"),
    (json.dumps({**DIRECT, "original_question": "replacement"}), "completed"),
    (json.dumps({**DECOMPOSED, "queries": [{"query_id": "q", "text": "x", "requirement_ids": ["unknown"]}]}), "completed"),
    ("", "completed"),
])
def test_invalid_or_incomplete_planning_has_no_repair_or_fallback(output, status):
    sdk = Mock()
    sdk.with_options.return_value = sdk
    sdk.responses.create.return_value = response(output, status=status)
    with pytest.raises((ValueError, RuntimeError)):
        PlannerClient(sdk, "model", PlanningOptions(), "cl100k_base").plan("Question", "Question", lambda: 20)
    sdk.responses.create.assert_called_once()
    assert sdk.with_options.call_args.kwargs["max_retries"] == 0


def test_input_cap_rejects_before_model_call():
    sdk = Mock()
    with pytest.raises(ValueError, match="too large"):
        PlannerClient(sdk, "model", PlanningOptions(max_input_tokens=1), "cl100k_base").plan("Question", "Question", lambda: 20)
    sdk.with_options.assert_not_called()


def test_direct_and_narrowing_decisions_do_not_invent_queries():
    assert PlanDecision(**DIRECT).to_plan("original", "resolved").queries[0].text == "resolved"
    assert PlanDecision(**{**DIRECT, "route": "needs_narrowing"}).to_plan("original", "resolved") is None
    with pytest.raises(ValueError):
        PlanDecision(**{**DECOMPOSED, "route": "direct"}).to_plan("original", "resolved")


@pytest.fixture
def planned_api(configured_app):
    app, embeddings, sdk = configured_app
    sdk.with_options.return_value = sdk
    embeddings.bounded.return_value = embeddings
    decisions = [DECOMPOSED]
    def generate(**kwargs):
        if "text" in kwargs:
            return response(json.dumps(decisions[0]))
        if "history" in kwargs["input"][-1]["content"]:
            return response("Explain the training method and evaluation result.")
        return response("Labeled examples were used. Accuracy was 90%. [1]")
    sdk.responses.create.side_effect = generate
    with TestClient(app) as client:
        resources = app.state.resources
        streaming = Mock()
        streaming.bounded.return_value = streaming
        async def stream(_messages):
            yield "Labeled examples were used. Accuracy was 90%. [1]"
        streaming.stream = stream
        resources.streaming_llm = streaming
        file = client.post("/api/files", files={"file": ("experiment.txt", b"Training method: labeled examples. Evaluation result: accuracy 90%.", "text/plain")}).json()
        embeddings.embed_query.reset_mock()
        yield client, resources, sdk, decisions, file["file_id"]


def test_json_and_saved_history_keep_exact_plan_sources_and_context(planned_api):
    client, resources, sdk, _, file_id = planned_api
    result = client.post("/api/chat", json={"question": "Describe the method and results.", "retrieval_mode": "planned"})
    assert result.status_code == 200, result.text
    answer = result.json()
    planning = answer["retrieval"]["planning"]
    assert len(planning["trace"]["runs"]) == 2
    assert planning["trace"]["allowed_file_ids"] == [file_id]
    assert planning["planner"]["usage"]["total_tokens"] == 77
    assert all(source["text"] in planning["context"] for source in answer["sources"])
    generation = [call.kwargs for call in sdk.responses.create.call_args_list if "text" not in call.kwargs][-1]
    assert planning["context"] in generation["input"][0]["content"]
    assert generation["max_output_tokens"] == 4096
    assert client.delete(f"/api/files/{file_id}").status_code == 204
    saved = client.get(f"/api/conversations/{answer['conversation_id']}").json()["messages"][-1]
    assert saved["retrieval"]["planning"] == planning
    assert all(source["file_deleted"] for source in saved["sources"])


def events_from(response):
    events = []
    for frame in response.text.strip().split("\n\n"):
        event, data = frame.split("\n")
        events.append({"event": event.removeprefix("event: "), **json.loads(data.removeprefix("data: "))})
    return events


def test_stream_sources_complete_and_history_agree(planned_api):
    client, _, _, _, _ = planned_api
    result = client.post("/api/chat/stream", json={"question": "Method and results?", "request_id": "planned-stream", "retrieval_mode": "planned"})
    events = events_from(result)
    assert [event["event"] for event in events][:4] == ["start", "progress", "progress", "sources"]
    sources = next(event for event in events if event["event"] == "sources")
    complete = events[-1]
    assert complete["event"] == "complete"
    assert sources["sources"] == complete["sources"]
    assert sources["retrieval"] == complete["retrieval"]
    saved = client.get(f"/api/conversations/{complete['conversation_id']}").json()["messages"][-1]
    assert saved["retrieval"] == complete["retrieval"]


def test_followup_resolves_before_planning(planned_api):
    client, _, sdk, _, _ = planned_api
    first = client.post("/api/chat", json={"question": "Explain training.", "retrieval_mode": "planned"}).json()
    answer = client.post("/api/chat", json={"question": "What about its results?", "conversation_id": first["conversation_id"], "retrieval_mode": "planned"}).json()
    trace = answer["retrieval"]["planning"]["trace"]
    assert trace["plan"]["original_question"] == "What about its results?"
    assert trace["plan"]["resolved_question"] == "Explain the training method and evaluation result."
    planner_calls = [call.kwargs for call in sdk.responses.create.call_args_list if "text" in call.kwargs]
    assert len(planner_calls) == 2


def test_api_configured_mode_can_be_overridden(planned_api):
    client, resources, sdk, _, _ = planned_api
    resources.settings.retrieval_mode = "planned"
    planned = client.post("/api/chat", json={"question": "Method and results?"}).json()
    assert planned["retrieval"]["planning"] is not None
    sdk.responses.create.reset_mock()
    single = client.post("/api/chat", json={"question": "Method?", "retrieval_mode": "single"}).json()
    assert single["retrieval"]["planning"] is None
    assert all("text" not in call.kwargs for call in sdk.responses.create.call_args_list)


def test_cli_planned_flag_uses_the_same_controller(tmp_path, monkeypatch):
    import sys
    from knowledgebase import cli
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("OPENAI_API_KEY=offline\nPLANNER_MODEL=offline-planner\n")
    sdk = Mock()
    sdk.__enter__ = Mock(return_value=sdk)
    sdk.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(cli, "OpenAI", Mock(return_value=sdk))
    ask = Mock(return_value=SimpleNamespace(conversation_id="saved"))
    monkeypatch.setattr(cli, "answer_in_conversation", ask)
    monkeypatch.setattr(cli, "run_chat_loop", lambda callback: callback("Question"))
    monkeypatch.setattr(sys, "argv", ["main.py", "--retrieval-mode", "planned"])
    cli.cli()
    assert ask.call_args.kwargs["planner_client"].model == "offline-planner"
    assert ask.call_args.kwargs["planning_options"] == PlanningOptions()


def test_narrowing_does_not_search_or_generate(planned_api):
    client, resources, sdk, decisions, _ = planned_api
    decisions[0] = {**DIRECT, "route": "needs_narrowing"}
    result = client.post("/api/chat", json={"question": "Compare many dimensions.", "retrieval_mode": "planned"}).json()
    assert result["answer"] == NARROWING_MESSAGE and result["sources"] == []
    assert result["retrieval"]["planning"]["trace"] is None
    resources.embeddings.embed_query.assert_not_called()
    sdk.responses.create.assert_called_once()


def test_unresolved_scope_skips_planner_and_single_mode_is_unchanged(planned_api):
    client, _, sdk, _, _ = planned_api
    response = client.post("/api/chat", json={"question": "In missing.pdf, explain the results.", "retrieval_mode": "planned"})
    assert response.status_code == 200
    assert response.json()["retrieval"]["document_scope"]["status"] == "not_found"
    sdk.responses.create.assert_not_called()
    single = client.post("/api/chat", json={"question": "Explain the result.", "retrieval_mode": "single"}).json()
    assert single["retrieval"]["planning"] is None
    assert all("text" not in call.kwargs for call in sdk.responses.create.call_args_list)


def test_invalid_plan_never_persists_a_success(planned_api):
    client, resources, _, decisions, _ = planned_api
    decisions[0] = {"bad": "plan"}
    result = client.post("/api/chat/stream", json={"question": "Explain results.", "retrieval_mode": "planned", "request_id": "invalid"})
    assert events_from(result)[-1]["event"] == "error"
    with resources.sessions() as session:
        assert session.scalar(select(func.count()).select_from(MessageRecord)) == 0


@pytest.mark.anyio
@pytest.mark.parametrize("cancel_at", ["planner", "query"])
async def test_cancellation_prevents_later_queries_generation_and_persistence(planned_api, cancel_at):
    _, resources, _, _, _ = planned_api
    started, release, returned = Event(), Event(), Event()
    target = resources.planner if cancel_at == "planner" else resources.embeddings
    method = "plan" if cancel_at == "planner" else "embed_query"
    original = getattr(target, method)
    def blocked(*args, **kwargs):
        started.set()
        release.wait(3)
        try:
            return original(*args, **kwargs)
        finally:
            returned.set()
    wrapped = Mock(side_effect=blocked)
    setattr(target, method, wrapped)
    events = []
    stream = await stream_answer_in_conversation("Method and result?", "cancel", resources.sessions,
        resources.embeddings, resources.store, resources.llm, resources.streaming_llm, planner_client=resources.planner)
    async def consume():
        async with aclosing(stream):
            async for event in stream:
                events.append(event.event)
    try:
        async with anyio.create_task_group() as tasks:
            tasks.start_soon(consume)
            assert await anyio.to_thread.run_sync(started.wait, 2)
            tasks.cancel_scope.cancel()
    finally:
        release.set()
        assert await anyio.to_thread.run_sync(returned.wait, 2)
    assert "complete" not in events
    assert wrapped.call_count == 1
    with resources.sessions() as session:
        assert session.scalar(select(func.count()).select_from(MessageRecord)) == 0


def test_settings_nested_planning_limits(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("OPENAI_API_KEY=offline\nRETRIEVAL_MODE=planned\nPLANNING__MAX_OUTPUT_TOKENS=1234\n")
    settings = Settings()
    assert settings.retrieval_mode == "planned" and settings.planning.max_output_tokens == 1234
    with pytest.raises(ValueError):
        PlanningOptions(request_timeout_seconds=10, answer_reserve_seconds=10)


@pytest.mark.anyio
@pytest.mark.parametrize("timeout_at", ["planner", "query"])
async def test_search_deadline_stops_without_persisting(planned_api, timeout_at):
    _, resources, _, _, _ = planned_api
    release, returned = Event(), Event()
    target = resources.planner if timeout_at == "planner" else resources.embeddings
    method = "plan" if timeout_at == "planner" else "embed_query"
    original = getattr(target, method)
    def blocked(*args, **kwargs):
        release.wait(3)
        try:
            return original(*args, **kwargs)
        finally:
            returned.set()
    wrapped = Mock(side_effect=blocked)
    setattr(target, method, wrapped)
    stream = await stream_answer_in_conversation("Method and result?", "timeout", resources.sessions,
        resources.embeddings, resources.store, resources.llm, resources.streaming_llm,
        planner_client=resources.planner,
        planning_options=PlanningOptions(request_timeout_seconds=0.3, answer_reserve_seconds=0.1))
    try:
        events = [event async for event in stream]
    finally:
        release.set()
        assert await anyio.to_thread.run_sync(returned.wait, 2)
    assert events[-1].event == "error" and "timed out" in events[-1].data["message"]
    assert wrapped.call_count == 1
    with resources.sessions() as session:
        assert session.scalar(select(func.count()).select_from(MessageRecord)) == 0


def test_bounded_answer_disables_sdk_retries():
    from openai import InternalServerError
    from knowledgebase.providers.llm import LLMClient
    from knowledgebase.providers.limits import GenerationLimits
    attempts = []
    def fail(request):
        attempts.append(json.loads(request.content))
        return httpx2.Response(500, json={"error": {"message": "offline failure"}})
    with OpenAI(api_key="offline", http_client=httpx2.Client(transport=httpx2.MockTransport(fail))) as sdk:
        base = LLMClient(sdk, "model")
        bounded = base.bounded(GenerationLimits(lambda: 1, 100, 32, "cl100k_base"))
        with pytest.raises(InternalServerError):
            bounded.generate([{"role": "user", "content": "Question"}])
        assert base._limits is None
    assert len(attempts) == 1 and attempts[0]["max_output_tokens"] == 32


@pytest.mark.anyio
async def test_final_generation_deadline_closes_stalled_stream():
    from test_llm_streaming import EventBody, client
    from knowledgebase.providers.llm import StreamingLLMClient
    from knowledgebase.services.planning import RequestControl
    body, requests = EventBody("response.completed"), []
    body.wait = anyio.Event()
    control = RequestControl(PlanningOptions(request_timeout_seconds=0.2, answer_reserve_seconds=0.1), "cl100k_base")
    async with client(body, requests) as sdk:
        bounded = StreamingLLMClient(sdk, "model").bounded(control.generation_limits())
        with pytest.raises(TimeoutError):
            async for _ in bounded.stream([]):
                pass
    assert body.closed and len(requests) == 1
    assert requests[0]["max_output_tokens"] == 4096
