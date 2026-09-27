"""Packed-context assessment and bounded gap searches, with offline provider outputs."""
from contextlib import aclosing
from copy import deepcopy
import json
import re
from threading import Event

import anyio
import pytest
from sqlalchemy import func, select

from knowledgebase.config import PlanningOptions
from knowledgebase.rag.generation import INSUFFICIENT_EVIDENCE
from knowledgebase.rag.sufficiency import SufficiencyAssessment, assessment_excerpts, validate_assessment
from knowledgebase.services.chat import stream_answer_in_conversation
from knowledgebase.storage.models import MessageRecord
from knowledgebase.storage.operations import update_file_status
from test_automatic_planning import DIRECT, response, events_from
from test_dependent_retrieval import hop_api, ask, QUESTION, PLAN, DOCUMENTS


def payload_catalog(payload):
    """Read the test provider's ID selections from the annotated source context."""
    entries = []
    for line in payload["context"].splitlines(keepends=True):
        if line.startswith("Source metadata: "):
            file_name = json.loads(line.removeprefix("Source metadata: "))["file_name"]
        match = re.match(r"\[(p\d+)\] (.*)", line, flags=re.DOTALL)
        if match:
            entries.append({"evidence_id": match[1], "file_name": file_name, "text": match[2]})
    return entries


def unannotated_context(payload):
    return re.sub(r"(?m)^\[p\d+\] ", "", payload["context"])


@pytest.fixture
def assessed_api(hop_api):
    client, resources, sdk, choices, bindings, files = hop_api
    resources.settings.planning.sufficiency_enabled = True
    original = sdk.responses.create.side_effect
    assessments = []
    choices.update(assessment=None, assessment_hook=None)
    def generate(**kwargs):
        if kwargs.get("text", {}).get("format", {}).get("name") != "evidence_assessment":
            return original(**kwargs)
        payload = json.loads(kwargs["input"][-1]["content"])
        assessments.append(payload)
        if choices["assessment_hook"]:
            choices["assessment_hook"]()
        if choices["assessment"]:
            decision = choices["assessment"](payload)
        else:
            decision = {"requirements": [], "queries": []}
            for requirement in payload["requirements"]:
                index = {"winner": 0, "employer": 1, "location": 2}.get(requirement["requirement_id"], 0)
                excerpt = next((e for e in payload_catalog(payload) if e["file_name"] == DOCUMENTS[index][0]), None)
                decision["requirements"].append({"requirement_id": requirement["requirement_id"],
                    "status": "supported" if excerpt else "missing", "gap": "" if excerpt else "No supporting excerpt.",
                    "references": [{"evidence_id": excerpt["evidence_id"]}] if excerpt else []})
        return response(json.dumps(decision))
    sdk.responses.create.side_effect = generate
    yield client, resources, sdk, choices, bindings, files, assessments


def one_point(choices):
    choices["plan"] = {"route": "decomposed", "requirements": [PLAN["requirements"][2]],
        "queries": [{"query_id": "initial", "text": "Aster Prize winner", "requirement_ids": ["location"]}], "dependencies": []}


def missing(payload, queries=()):
    return {"requirements": [{"requirement_id": r["requirement_id"], "status": "missing",
        "gap": "Location is absent.", "references": []} for r in payload["requirements"]], "queries": list(queries)}


def supplement(text="Aster Prize location"):
    return {"requirement_ids": ["location"], "query_template": text, "target": "", "references": []}


def test_assess_each_hop_then_generate_from_same_final_context(assessed_api):
    client, resources, sdk, _, bindings, _, assessments = assessed_api
    answer = ask(client).json()
    planning = answer["retrieval"]["planning"]
    assert planning["version"] == 3
    assert len(assessments) == 3 and len(bindings) == 2
    assert planning["hops"]["stop_reason"] == "requirements_supported"
    assert planning["assessment"]["context"] == planning["context"] == unannotated_context(assessments[-1])
    assert [r["status"] for r in planning["assessment"]["requirements"]] == ["supported"] * 3
    message = sdk.responses.create.call_args.kwargs["input"][0]["content"]
    assert planning["context"] in message and "fallible guidance" in message
    assert "evidence_catalog" not in message
    assert resources.embeddings.embed_query.call_count == 3
    saved = client.get(f"/api/conversations/{answer['conversation_id']}").json()["messages"][-1]
    assert saved["retrieval"] == answer["retrieval"]


def test_single_supported_pass_skips_remaining_dependencies(assessed_api):
    client, resources, _, choices, bindings, _, assessments = assessed_api
    choices["plan"] = {"route": "direct", "requirements": [], "queries": [], "dependencies": []}
    answer = ask(client).json()
    assert answer["retrieval"]["planning"]["hops"]["stop_reason"] == "requirements_supported"
    assert resources.embeddings.embed_query.call_count == 1 and len(assessments) == 1 and not bindings


def test_source_bound_supplement_fills_gap(assessed_api):
    client, resources, _, choices, _, _, assessments = assessed_api
    one_point(choices)
    def assess(payload):
        excerpt = payload_catalog(payload)[0]
        if len(payload["executed_queries"]) == 1:
            return missing(payload, [{"requirement_ids": ["location"], "query_template": "Who employs {target}?",
                "target": "Mira Cole", "references": [{"evidence_id": excerpt["evidence_id"]}]}])
        staff = next(e for e in payload_catalog(payload) if e["file_name"] == "staff.txt")
        if len(payload["executed_queries"]) == 2:
            return missing(payload, [{"requirement_ids": ["location"], "query_template": "Where is {target} located?",
                "target": "Birch Institute", "references": [{"evidence_id": staff["evidence_id"]}]}])
        place = next(e for e in payload_catalog(payload) if e["file_name"] == "place.txt")
        return {"requirements": [{"requirement_id": "location", "status": "supported", "gap": "",
            "references": [{"evidence_id": place["evidence_id"]}]}], "queries": []}
    choices["assessment"] = assess
    answer = ask(client).json()
    planning = answer["retrieval"]["planning"]
    assert planning["hops"]["stop_reason"] == "requirements_supported"
    assert len(assessments) == 3 and resources.embeddings.embed_query.call_count == 3
    assert {s["file_name"] for s in answer["sources"]} == {"award.txt", "staff.txt", "place.txt"}
    assert len(planning["hops"]["supplementary_queries"]) == 2


@pytest.mark.parametrize("status", ["partial", "conflicting"])
def test_partial_or_conflicting_guidance_reaches_answer(assessed_api, status):
    client, _, sdk, choices, _, _, _ = assessed_api
    choices["plan"] = deepcopy(DIRECT)
    def assess(payload):
        refs = [{"evidence_id": e["evidence_id"]}
                for e in payload_catalog(payload)[:2 if status == "conflicting" else 1]]
        # The mocked status tests transport/provenance, not the semantic truth of a conflict.
        return {"requirements": [{"requirement_id": "answer", "status": status,
            "gap": "A requested detail is unresolved.", "references": refs}], "queries": []}
    choices["assessment"] = assess
    answer = ask(client).json()
    assert answer["retrieval"]["planning"]["assessment"]["requirements"][0]["status"] == status
    assert status in sdk.responses.create.call_args.kwargs["input"][0]["content"]
    assert answer["retrieval"]["planning"]["hops"]["stop_reason"] == "no_eligible_query"


def test_all_missing_abstains_despite_irrelevant_retrieval(assessed_api):
    client, _, sdk, choices, _, _, _ = assessed_api
    one_point(choices)
    choices["assessment"] = missing
    answer = ask(client).json()
    assert answer["sources"] and answer["answer"] == INSUFFICIENT_EVIDENCE
    assert all("text" in call.kwargs for call in sdk.responses.create.call_args_list)


@pytest.mark.parametrize("corrupt", [
    lambda a: a["requirements"][0].update(requirement_id="unknown"),
    lambda a: a["requirements"].append(a["requirements"][0]),
    lambda a: a["requirements"][0]["references"][0].update(evidence_id="excluded-source"),
    lambda a: a["requirements"][0]["references"][0].update(quote="A fact never supplied."),
    lambda a: a.update(queries=[supplement("Where is an invented {target}?")]),
])
def test_invalid_assessment_fails_without_repair_or_history(assessed_api, corrupt):
    client, resources, _, choices, _, _, assessments = assessed_api
    one_point(choices)
    def assess(payload):
        a = {"requirements": [{"requirement_id": "location", "status": "partial", "gap": "Missing location.",
            "references": [{"evidence_id": payload_catalog(payload)[0]["evidence_id"]}]}], "queries": []}
        corrupt(a)
        return a
    choices["assessment"] = assess
    assert ask(client).status_code == 500 and len(assessments) == 1
    with resources.sessions() as session:
        assert session.scalar(select(func.count()).select_from(MessageRecord)) == 0


@pytest.mark.parametrize("mode", ["duplicate", "no_progress", "query_limit", "round_limit"])
def test_limits_stop_further_queries_and_assess_final_context(assessed_api, mode):
    client, resources, _, choices, _, _, assessments = assessed_api
    one_point(choices)
    if mode == "round_limit":
        resources.settings.planning.max_rounds = 1
    choices["assessment"] = lambda p: missing(p, [supplement("Aster Prize winner" if mode == "duplicate" else f"Aster Prize location {i}")
        for i in range(6 if mode == "query_limit" else 1)])
    answer = ask(client).json()
    planning = answer["retrieval"]["planning"]
    assert planning["hops"]["stop_reason"] == {"duplicate": "no_eligible_query", "no_progress": "no_new_evidence",
        "query_limit": "query_limit", "round_limit": "round_limit"}[mode]
    assert resources.embeddings.embed_query.call_count == (6 if mode == "query_limit" else 2 if mode == "no_progress" else 1)
    assert unannotated_context(assessments[-1]) == planning["context"]


def test_supplements_keep_explicit_file_scope(assessed_api):
    client, _, _, choices, _, files, _ = assessed_api
    one_point(choices)
    choices["assessment"] = lambda p: missing(p, [supplement("Where is Birch Institute located?")])
    answer = ask(client, file_ids=[files[0]]).json()
    assert {s["file_id"] for s in answer["sources"]} == {files[0]}
    assert answer["retrieval"]["planning"]["hops"]["stop_reason"] == "no_new_evidence"


def test_budget_excluded_text_is_not_assessed(assessed_api):
    client, resources, _, _, _, _, assessments = assessed_api
    resources.settings.evidence_max_tokens = 1
    answer = ask(client).json()
    assert answer["answer"] == INSUFFICIENT_EVIDENCE and not answer["sources"] and not assessments
    assert answer["retrieval"]["planning"]["assessment"]["record"] is None


def test_deletion_between_assessment_and_search_removes_target(assessed_api):
    client, resources, _, choices, _, files, assessments = assessed_api
    one_point(choices)
    def assess(payload):
        with resources.sessions.begin() as session:
            update_file_status(session, files[0], "failed")
        return missing(payload, [{"requirement_ids": ["location"], "query_template": "Who employs {target}?",
            "target": "Mira Cole", "references": [{"evidence_id": payload_catalog(payload)[0]["evidence_id"]}]}])
    choices["assessment"] = assess
    answer = ask(client).json()
    assert not answer["sources"] and len(assessments) == 1
    assert resources.embeddings.embed_query.call_count == 1
    planning = answer["retrieval"]["planning"]
    assert planning["assessment"]["context"] == planning["context"] == ""
    assert planning["hops"]["supplementary_queries"][0]["excluded_reason"] == "evidence_unavailable"


def test_stream_assessment_progress_final_sources_and_history(assessed_api):
    client, _, _, _, _, files, _ = assessed_api
    events = events_from(client.post("/api/chat/stream", json={"question": QUESTION, "retrieval_mode": "planned", "request_id": "assess"}))
    assert sum(e["event"] == "progress" and e["stage"] == "assessing" for e in events) == 3
    assert sum(e["event"] == "sources" for e in events) == 1 and events[-1]["event"] == "complete"
    assert next(e["retrieval"] for e in events if e["event"] == "sources") == events[-1]["retrieval"]
    for identity in files:
        client.delete(f"/api/files/{identity}")
    saved = client.get(f"/api/conversations/{events[-1]['conversation_id']}").json()["messages"][-1]
    assert saved["retrieval"] == events[-1]["retrieval"]


@pytest.mark.anyio
@pytest.mark.parametrize("stop", ["cancel", "timeout"])
async def test_cancel_during_assessment_does_not_continue_or_save(assessed_api, stop):
    _, resources, _, choices, _, _, _ = assessed_api
    started, release, returned = Event(), Event(), Event()
    def hook():
        started.set(); release.wait(3); returned.set()
    choices["assessment_hook"] = hook
    options = PlanningOptions(request_timeout_seconds=0.8, answer_reserve_seconds=0.1) if stop == "timeout" else PlanningOptions()
    stream = await stream_answer_in_conversation(QUESTION, "stop-assessment", resources.sessions,
        resources.embeddings, resources.store, resources.llm, resources.streaming_llm,
        planner_client=resources.planner, planning_options=options, retrieval_options=resources.settings.retrieval_options, top_k=3)
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
    assert not any(e.event in {"complete", "sources", "answer_delta"} for e in events)
    if stop == "timeout":
        assert events[-1].event == "error" and "timed out" in events[-1].data["message"]
    assert resources.embeddings.embed_query.call_count == 1
    with resources.sessions() as session:
        assert session.scalar(select(func.count()).select_from(MessageRecord)) == 0


def test_direct_plan_merges_supplementary_candidates(hop_api):
    from knowledgebase.rag.planning import PlannedQuery, direct_plan
    from knowledgebase.rag.planned_retrieval import retrieve_plan
    _, resources, _, _, _, files = hop_api
    plan = direct_plan(QUESTION)
    plan.queries[0].file_ids = [files[0]]
    with resources.sessions() as session:
        initial = retrieve_plan(plan, session, resources.embeddings, resources.store,
            top_k=3, retrieval_options=resources.settings.retrieval_options)
        final = retrieve_plan(plan, session, resources.embeddings, resources.store,
            top_k=3, retrieval_options=resources.settings.retrieval_options, previous_runs=initial.trace.runs,
            queries=[PlannedQuery(query_id="extra", text="Mira Cole employer", requirement_ids=["answer"], file_ids=[files[1]])])
    assert {h.file_name for h in final.evidence.chunks} == {"award.txt", "staff.txt"}


def test_assessment_catalog_includes_pdf_supplement_offsets():
    from types import SimpleNamespace
    from knowledgebase.rag.planning import AnswerRequirement
    from knowledgebase.schemas import PdfRegion

    result = SimpleNamespace(evidence=SimpleNamespace(chunks=[SimpleNamespace(
        chunk=SimpleNamespace(file_id="pdf", start_offset=100, end_offset=110, text="Value: 42."),
        file_name="report.pdf", pdf=SimpleNamespace(
            regions=[PdfRegion(start_offset=100, end_offset=110, page_index=1, bbox=(1, 1, 10, 10), precision="cell")],
            supplements=[SimpleNamespace(start_offset=10, end_offset=25, text="USD in millions",
                regions=[PdfRegion(start_offset=10, end_offset=25, page_index=0, bbox=(1, 1, 10, 10), precision="block")])]))]))
    excerpts = assessment_excerpts(result)
    requirements, _ = validate_assessment(SufficiencyAssessment(requirements=[{
        "requirement_id": "unit", "status": "supported", "gap": "", "references": [{
            "evidence_id": next(e["evidence_id"] for e in excerpts if e["text"] == "USD in millions")}]}], queries=[]),
        [AnswerRequirement(requirement_id="unit", description="Table units")], excerpts)
    assert requirements[0]["references"][0]["start_offset"] == 10
    assert requirements[0]["references"][0]["end_offset"] == 25
    assert requirements[0]["references"][0]["quote"] == "USD in millions"
    assert requirements[0]["references"][0]["page_indices"] == [0]
    assert excerpts[0]["source_number"] == excerpts[1]["source_number"] == 1


def test_assessment_schema_through_real_sdk_offline_transport():
    import httpx
    from openai import OpenAI
    from knowledgebase.providers.planner import PlannerClient
    from test_automatic_planning import sdk_response
    calls = []
    def handle(request):
        payload = json.loads(request.content)
        calls.append(payload)
        schema = payload["text"]["format"]["schema"]
        for model in [schema, *schema["$defs"].values()]:
            assert set(model["required"]) == set(model["properties"])
            assert model["additionalProperties"] is False
        assert set(schema["$defs"]["PassageReference"]["properties"]) == {"evidence_id"}
        assert payload["text"]["format"]["strict"] is True
        return httpx.Response(200, json=sdk_response(json.dumps(missing({"requirements": [{"requirement_id": "a"}]}))))
    with OpenAI(api_key="offline", base_url="https://offline.test/v1",
                http_client=httpx.Client(transport=httpx.MockTransport(handle))) as sdk:
        planner = PlannerClient(sdk, "requested-model", PlanningOptions(), "cl100k_base")
        _, record = planner.structured(SufficiencyAssessment, "evidence_assessment", "Assess.", {},
            lambda: 10, prompt_version="evidence-sufficiency-v3")
    assert len(calls) == 1 and record["usage"]["total_tokens"] == 77
    assert record["max_retries"] == 0 and record["billed_cost"] is None


def test_missing_stream_abstains_without_answer_provider(assessed_api):
    client, resources, _, choices, _, _, _ = assessed_api
    one_point(choices)
    choices["assessment"] = missing
    async def must_not_generate(_):
        raise AssertionError("All-missing evidence must not call the answer provider.")
        yield
    resources.streaming_llm.stream = must_not_generate
    events = events_from(client.post("/api/chat/stream", json={"question": QUESTION, "retrieval_mode": "planned", "request_id": "missing"}))
    assert events[-1]["event"] == "complete" and events[-1]["answer"] == INSUFFICIENT_EVIDENCE


def test_dependency_and_gap_queries_share_six_query_limit(assessed_api):
    client, resources, _, choices, _, _, assessments = assessed_api
    choices["assessment"] = lambda p: missing(p, [supplement(f"Aster Prize location {i}") for i in range(6)])
    answer = ask(client).json()
    planning = answer["retrieval"]["planning"]
    assert planning["hops"]["stop_reason"] == "query_limit"
    assert resources.embeddings.embed_query.call_count == 6 and len(assessments) == 2
    assert planning["hops"]["dependencies"][0]["status"] == "executed"
    assert any(q["excluded_reason"] == "query_limit" for q in planning["hops"]["supplementary_queries"])


def test_final_assessment_revokes_support_after_source_removed(assessed_api):
    client, resources, _, choices, _, files, assessments = assessed_api
    def remove_source():
        with resources.sessions.begin() as session:
            update_file_status(session, files[0], "failed")
    choices["binding_hook"] = remove_source
    answer = ask(client).json()
    planning = answer["retrieval"]["planning"]
    assert planning["hops"]["assessments"][0]["requirements"][0]["status"] == "supported"
    assert all(r["status"] == "missing" for r in planning["assessment"]["requirements"])
    assert not answer["sources"] and answer["answer"] == INSUFFICIENT_EVIDENCE
    assert len(assessments) == 1


def test_initial_context_can_satisfy_a_whole_dependency_chain(assessed_api):
    client, resources, _, _, bindings, _, assessments = assessed_api
    resources.settings.retrieval_candidate_limit = 3
    answer = ask(client).json()
    hops = answer["retrieval"]["planning"]["hops"]
    assert hops["stop_reason"] == "requirements_supported"
    assert [s["status"] for s in hops["dependencies"]] == ["not_needed", "not_needed"]
    assert resources.embeddings.embed_query.call_count == 1 and len(assessments) == 1 and not bindings


def test_question_filename_reformulation_does_not_require_a_source_target():
    from knowledgebase.rag.planning import AnswerRequirement

    requirements = [AnswerRequirement(requirement_id='grades', description='Grades in course.pdf')]
    value = {'requirements': [{'requirement_id': 'grades', 'status': 'missing',
                              'gap': 'Grade weights are absent.', 'references': []}],
             'queries': [{'requirement_ids': ['grades'], 'query_template': 'In course.pdf, find grade weights.',
                          'target': '', 'references': []}]}
    _, queries = validate_assessment(SufficiencyAssessment.model_validate(value), requirements, [])
    assert queries[0]['text'] == 'In course.pdf, find grade weights.'
    # This shape occurred in the live PDF run; keep rejecting unbound targets.
    value['queries'][0].update(query_template='In {target}, find grade weights.', target='course.pdf')
    with pytest.raises(ValueError):
        validate_assessment(SufficiencyAssessment.model_validate(value), requirements, [])


def test_separate_table_passage_ids_preserve_exact_source_spans():
    from types import SimpleNamespace

    from pydantic import ValidationError

    from knowledgebase.rag.planning import AnswerRequirement

    text = 'Three Months Ended\tTwelve Months Ended\nOther rows\nNet income\t$ 14,736\t$ 93,736'
    packed = SimpleNamespace(evidence=SimpleNamespace(chunks=[SimpleNamespace(
        chunk=SimpleNamespace(file_id='pdf', start_offset=0, end_offset=len(text), text=text),
        file_name='report.pdf', pdf=None)]))
    excerpts = assessment_excerpts(packed)
    selected = [excerpts[0], excerpts[-1]]
    requirements = [AnswerRequirement(requirement_id='income', description='Quarterly and annual net income')]
    def assessment(references):
        return SufficiencyAssessment.model_validate({'requirements': [{'requirement_id': 'income',
            'status': 'supported', 'gap': '', 'references': references}], 'queries': []})
    # The live response spliced headers and values; this output can now select only IDs.
    with pytest.raises(ValidationError):
        assessment([{'evidence_id': selected[0]['evidence_id'],
                     'quote': 'Three Months Ended\tTwelve Months Ended\n... Net income\t$ 14,736\t$ 93,736'}])
    result, _ = validate_assessment(assessment([{'evidence_id': e['evidence_id']} for e in selected]),
                                    requirements, excerpts)
    assert len(result[0]['references']) == 2
    assert [ref['quote'] for ref in result[0]['references']] == [text.splitlines(keepends=True)[0], text.splitlines()[-1]]
    for ref in result[0]['references']:
        assert text[ref['start_offset']:ref['end_offset']] == ref['quote']


def test_supplementary_target_must_occur_in_selected_passage():
    from types import SimpleNamespace

    from knowledgebase.rag.planning import AnswerRequirement

    text = DOCUMENTS[0][1]
    packed = SimpleNamespace(evidence=SimpleNamespace(chunks=[SimpleNamespace(
        chunk=SimpleNamespace(file_id='award', start_offset=40, end_offset=40 + len(text), text=text),
        file_name='award.txt', pdf=None)]))
    excerpts = assessment_excerpts(packed)
    requirements = [AnswerRequirement(requirement_id='employer', description='The prize winner employer')]
    value = {'requirements': [{'requirement_id': 'employer', 'status': 'missing',
                              'gap': 'The employer is absent.', 'references': []}],
             'queries': [{'requirement_ids': ['employer'], 'query_template': 'Who employs {target}?',
                          'target': 'Mira Cole', 'references': [{'evidence_id': excerpts[0]['evidence_id']}]}]}
    _, queries = validate_assessment(SufficiencyAssessment.model_validate(value), requirements, excerpts)
    assert queries[0]['text'] == 'Who employs Mira Cole?'
    assert queries[0]['references'][0]['quote'] == text
    assert queries[0]['references'][0]['start_offset'] == 40
    # Selecting a valid passage ID does not permit an entity absent from that passage.
    value['queries'][0]['target'] = 'Birch Institute'
    with pytest.raises(ValueError):
        validate_assessment(SufficiencyAssessment.model_validate(value), requirements, excerpts)
