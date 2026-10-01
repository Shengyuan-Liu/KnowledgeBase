"""Source-bound multi-hop retrieval with real storage and offline model responses."""
from contextlib import aclosing
from copy import deepcopy
import json
from threading import Event
from unittest.mock import Mock

import anyio
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import func, select

from knowledgebase.config import PlanningOptions
from knowledgebase.rag.dependencies import TargetDecision, adds_source_text, validate_binding
from knowledgebase.rag.planning import PlanDecision
from knowledgebase.services.chat import stream_answer_in_conversation
from knowledgebase.storage.models import MessageRecord
from knowledgebase.storage.operations import update_file_status
from test_automatic_planning import response, events_from

QUESTION = "Where is the institute employing the Aster Prize winner located?"
PLAN = {
    "route": "dependent", "requirements": [
        {"requirement_id": "winner", "description": "Prize winner"},
        {"requirement_id": "employer", "description": "Winner's institute"},
        {"requirement_id": "location", "description": "Institute location"}],
    "queries": [{"query_id": "winner", "text": "Aster Prize winner", "requirement_ids": ["winner"]}],
    "dependencies": [
        {"query_id": "employer", "query_template": "Who employs {target}?", "requirement_ids": ["employer"], "depends_on": ["winner"]},
        {"query_id": "location", "query_template": "Where is {target} located?", "requirement_ids": ["location"], "depends_on": ["employer"]}],
}
DOCUMENTS = [
    ("award.txt", "The Aster Prize winner is Mira Cole.", [1., 0., 0.]),
    ("staff.txt", "Mira Cole works at Birch Institute.", [0., 1., 0.]),
    ("place.txt", "Birch Institute is in Oslo.", [0., 0., 1.]),
]


@pytest.fixture
def hop_api(configured_app):
    app, embeddings, sdk = configured_app
    sdk.with_options.return_value = sdk
    embeddings.bounded.return_value = embeddings
    embeddings.embed_documents.side_effect = None
    choices = {"plan": deepcopy(PLAN), "target_status": "resolved", "corrupt": None, "binding_hook": None}
    bindings = []
    def generate(**kwargs):
        if "text" in kwargs:
            if kwargs["text"]["format"]["name"] == "retrieval_plan":
                return response(json.dumps(choices["plan"]))
            payload = json.loads(kwargs["input"][-1]["content"])
            bindings.append(payload)
            if choices["binding_hook"]:
                choices["binding_hook"]()
            decisions = []
            for item in payload["pending_queries"]:
                target = "Mira Cole" if item["query_id"].startswith("employer") else "Birch Institute"
                excerpt = next(e for e in item["evidence"] if target in e["text"])
                decision = {"query_id": item["query_id"], "status": choices["target_status"],
                    "target": target if choices["target_status"] == "resolved" else "",
                    "references": [{"evidence_id": excerpt["evidence_id"], "quote": excerpt["text"]}]
                        if choices["target_status"] == "resolved" else []}
                if choices["corrupt"]:
                    choices["corrupt"](decision)
                decisions.append(decision)
            return response(json.dumps({"decisions": decisions}))
        return response("The institute is in Oslo. [3]" if "Oslo" in kwargs["input"][0]["content"] else "The location is not provided. [1]")
    sdk.responses.create.side_effect = generate
    with TestClient(app) as client:
        resources = app.state.resources
        resources.settings.planning.sufficiency_enabled = False
        resources.settings.retrieval_strategy = "vector"
        resources.settings.retrieval_candidate_limit = 1
        resources.settings.retrieval_top_k = 3
        files = []
        for name, text, vector in DOCUMENTS:
            embeddings.embed_documents.return_value = [vector]
            file = client.post("/api/files", files={"file": (name, text.encode(), "text/plain")}).json()
            files.append(file["file_id"])
        embeddings.embed_query.side_effect = lambda text: ([0., 0., 1.] if "Birch Institute" in text else
                                                          [0., 1., 0.] if "Mira Cole" in text else [1., 0., 0.])
        streaming = Mock()
        streaming.bounded.return_value = streaming
        async def stream(messages):
            yield "The institute is in Oslo. [3]" if "Oslo" in messages[0]["content"] else "The location is not provided. [1]"
        streaming.stream = stream
        resources.streaming_llm = streaming
        yield client, resources, sdk, choices, bindings, files


def ask(client, **extra):
    return client.post("/api/chat", json={"question": QUESTION, "retrieval_mode": "planned", **extra})


def test_three_hops_bind_exact_targets_and_persist_final_context(hop_api):
    client, resources, sdk, _, bindings, _ = hop_api
    answer = ask(client).json()
    planning = answer["retrieval"]["planning"]
    hops = planning["hops"]
    assert hops["stop_reason"] == "dependencies_complete"
    assert len(hops["rounds"]) == 3 and len(hops["bindings"]) == 2
    assert [c.args[0] for c in resources.embeddings.embed_query.call_args_list] == [
        "Aster Prize winner", "Who employs Mira Cole?", "Where is Birch Institute located?"]
    assert [s["file_name"] for s in answer["sources"]] == ["award.txt", "staff.txt", "place.txt"]
    assert all(s["references_in_final_context"] for s in hops["dependencies"])
    assert all("Oslo" not in json.dumps(p) for p in bindings)
    assert bindings[0]["pending_queries"][0]["prerequisite_queries"] == ["Aster Prize winner"]
    assert bindings[1]["pending_queries"][0]["prerequisite_queries"] == ["Who employs Mira Cole?"]
    generation = sdk.responses.create.call_args.kwargs["input"][0]["content"]
    assert planning["context"] in generation and "query_template" not in generation
    assert "The Aster Prize winner is Mira Cole." in hops["dependencies"][0]["references"][0]["quote"]
    saved = client.get(f"/api/conversations/{answer['conversation_id']}").json()["messages"][-1]
    assert saved["retrieval"] == answer["retrieval"]


def test_sse_publishes_only_final_sources_after_all_rounds(hop_api):
    client, _, _, _, _, files = hop_api
    events = events_from(client.post("/api/chat/stream", json={"question": QUESTION, "retrieval_mode": "planned", "request_id": "hops"}))
    assert [e["message"] for e in events if e["event"] == "progress" and e["message"].startswith("Searching round")] == [
        "Searching round 1…", "Searching round 2…", "Searching round 3…"]
    sources = [e for e in events if e["event"] == "sources"]
    assert len(sources) == 1 and len(sources[0]["sources"]) == 3
    assert events[-1]["event"] == "complete"
    assert sources[0]["retrieval"] == events[-1]["retrieval"]
    for file_id in files:
        client.delete(f"/api/files/{file_id}")
    saved = client.get(f"/api/conversations/{events[-1]['conversation_id']}").json()["messages"][-1]
    assert saved["retrieval"] == events[-1]["retrieval"]
    assert all(source["file_deleted"] for source in saved["sources"])


@pytest.mark.parametrize("status", ["missing", "ambiguous"])
def test_unresolved_target_does_not_guess_or_search(hop_api, status):
    client, resources, _, choices, bindings, _ = hop_api
    choices["target_status"] = status
    answer = ask(client).json()
    hops = answer["retrieval"]["planning"]["hops"]
    assert hops["stop_reason"] == "dependency_unresolved"
    assert hops["dependencies"][0]["status"] == status
    resources.embeddings.embed_query.assert_called_once_with("Aster Prize winner")
    assert len(bindings) == 1


@pytest.mark.parametrize("corrupt", [
    lambda d: d.update(target="Invented Institute"),
    lambda d: d["references"][0].update(evidence_id="not-supplied"),
    lambda d: d["references"][0].update(quote="Mira Cole won an unrelated award."),
    lambda d: d.update(query_id="unplanned"),
])
def test_invalid_target_is_an_error_without_repair_or_persistence(hop_api, corrupt):
    client, resources, _, choices, bindings, _ = hop_api
    choices["corrupt"] = corrupt
    assert ask(client).status_code == 500
    assert len(bindings) == 1 and resources.embeddings.embed_query.call_count == 1
    with resources.sessions() as session:
        assert session.scalar(select(func.count()).select_from(MessageRecord)) == 0


def test_scope_cannot_expand_to_follow_the_target(hop_api):
    client, resources, _, _, _, files = hop_api
    answer = ask(client, file_ids=[files[0]]).json()
    assert {s["file_id"] for s in answer["sources"]} == {files[0]}
    hops = answer["retrieval"]["planning"]["hops"]
    assert hops["stop_reason"] == "no_new_evidence" and len(hops["rounds"]) == 2
    assert resources.embeddings.embed_query.call_count == 2


def test_deleted_bridge_is_ineligible_before_next_query(hop_api):
    client, resources, _, choices, _, files = hop_api
    def delete_bridge():
        with resources.sessions.begin() as session:
            update_file_status(session, files[0], "failed")
    choices["binding_hook"] = delete_bridge
    answer = ask(client).json()
    hops = answer["retrieval"]["planning"]["hops"]
    assert hops["dependencies"][0]["status"] == "evidence_unavailable"
    assert not answer["sources"]
    assert resources.embeddings.embed_query.call_count == 1


def test_round_limit_and_budget_exclusion_do_not_bind_unseen_candidates(hop_api):
    client, resources, _, _, bindings, _ = hop_api
    resources.settings.planning.max_rounds = 1
    answer = ask(client).json()
    assert answer["retrieval"]["planning"]["hops"]["stop_reason"] == "round_limit"
    assert not bindings
    resources.settings.planning.max_rounds = 3
    resources.settings.evidence_max_tokens = 1
    answer = ask(client).json()
    assert answer["retrieval"]["planning"]["hops"]["stop_reason"] == "no_new_evidence"
    assert not answer["sources"] and not bindings


def test_topology_and_total_query_bounds():
    assert PlanDecision(**PLAN).to_plan(QUESTION, QUESTION).route == "dependent"
    bad = []
    cyclic = deepcopy(PLAN); cyclic["dependencies"][0]["depends_on"] = ["location"]; bad.append(cyclic)
    unknown = deepcopy(PLAN); unknown["dependencies"][0]["depends_on"] = ["unknown"]; bad.append(unknown)
    template = deepcopy(PLAN); template["dependencies"][0]["query_template"] = "Who employs a guessed name?"; bad.append(template)
    oversized = deepcopy(PLAN); oversized["queries"] *= 5; bad.append(oversized)
    deep = deepcopy(PLAN); deep["dependencies"].append({**deep["dependencies"][-1], "query_id": "four", "depends_on": ["location"]}); bad.append(deep)
    for value in bad:
        with pytest.raises(ValueError):
            PlanDecision(**value).to_plan(QUESTION, QUESTION)


def test_progress_uses_canonical_spans_not_chunk_identity():
    assert not adds_source_text({"a": [(5, 15)]}, {"a": [(0, 10), (8, 20)]})
    assert adds_source_text({"a": [(5, 21)]}, {"a": [(0, 10), (8, 20)]})
    assert adds_source_text({"a": [(0, 10)]}, {"a": [(0, 4), (5, 10)]})
    excerpt = {"evidence_id": "a@10:30", "file_id": "a", "file_name": "award.txt", "start_offset": 10, "text": "Winner: Mira Cole."}
    refs = validate_binding(TargetDecision(query_id="q", status="resolved", target="Mira Cole",
        references=[{"evidence_id": "a@10:30", "quote": "Mira Cole"}]), [excerpt])
    assert refs[0]["start_offset"] == 18 and refs[0]["end_offset"] == 27


@pytest.mark.anyio
@pytest.mark.parametrize("stop", ["cancel", "timeout"])
async def test_stop_during_binding_never_starts_dependent_search(hop_api, stop):
    _, resources, _, choices, _, _ = hop_api
    started, release, returned = Event(), Event(), Event()
    def wait_for_stop():
        started.set()
        release.wait(3)
        returned.set()
    choices["binding_hook"] = wait_for_stop
    options = PlanningOptions(request_timeout_seconds=0.8, answer_reserve_seconds=0.1) if stop == "timeout" else PlanningOptions()
    options.sufficiency_enabled = False
    stream = await stream_answer_in_conversation(QUESTION, "stop-hops", resources.sessions,
        resources.embeddings, resources.store, resources.llm, resources.streaming_llm,
        planner_client=resources.planner, planning_options=options,
        retrieval_options=resources.settings.retrieval_options, top_k=3)
    events = []
    async def consume():
        async with aclosing(stream):
            async for event in stream:
                events.append(event)
    try:
        async with anyio.create_task_group() as tasks:
            tasks.start_soon(consume)
            assert await anyio.to_thread.run_sync(started.wait, 2)
            if stop == "cancel":
                tasks.cancel_scope.cancel()
    finally:
        release.set()
        assert await anyio.to_thread.run_sync(returned.wait, 2)
    assert not any(e.event == "complete" for e in events)
    if stop == "timeout":
        assert events[-1].event == "error" and "timed out" in events[-1].data["message"]
    assert resources.embeddings.embed_query.call_count == 1
    with resources.sessions() as session:
        assert session.scalar(select(func.count()).select_from(MessageRecord)) == 0


def test_direct_service_matches_api_controller(hop_api):
    from knowledgebase.services.chat import answer_in_conversation
    _, resources, _, _, _, _ = hop_api
    result = answer_in_conversation(QUESTION, resources.sessions, resources.embeddings, resources.store,
        resources.llm, planner_client=resources.planner, planning_options=resources.settings.planning,
        retrieval_options=resources.settings.retrieval_options, top_k=3)
    assert result.retrieval.planning["hops"]["stop_reason"] == "dependencies_complete"


def test_duplicate_query_across_rounds_does_not_repeat_embedding(hop_api):
    client, resources, _, choices, _, _ = hop_api
    choices["plan"]["queries"][0]["text"] = "Who employs Mira Cole?"
    answer = ask(client).json()
    hops = answer["retrieval"]["planning"]["hops"]
    assert hops["stop_reason"] == "no_new_evidence"
    resources.embeddings.embed_query.assert_called_once_with("Who employs Mira Cole?")
    assert answer["retrieval"]["planning"]["trace"]["runs"][0]["query_ids"] == ["winner", "employer"]


def test_parallel_dependencies_share_one_binding_call(hop_api):
    client, resources, _, choices, bindings, _ = hop_api
    choices["plan"]["dependencies"][1] = {
        "query_id": "employer_alt", "query_template": "Where does {target} work?",
        "requirement_ids": ["location"], "depends_on": ["winner"]}
    answer = ask(client).json()
    assert len(bindings) == 1 and len(bindings[0]["pending_queries"]) == 2
    assert len(answer["retrieval"]["planning"]["hops"]["rounds"]) == 2
    assert resources.embeddings.embed_query.call_count == 3


def test_every_prerequisite_needs_supplied_evidence(hop_api):
    client, resources, _, choices, bindings, _ = hop_api
    choices["plan"]["queries"].append({"query_id": "empty", "text": 'In "missing.txt", find the winner.', "requirement_ids": ["winner"]})
    choices["plan"]["dependencies"][0]["depends_on"].append("empty")
    answer = ask(client).json()
    assert not bindings
    assert answer["retrieval"]["planning"]["hops"]["dependencies"][0]["status"] == "missing"
    assert resources.embeddings.embed_query.call_count == 1
