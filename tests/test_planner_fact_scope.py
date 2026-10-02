"""Exercise recorded plan-scope failures and annotated downstream contracts."""

import json
from pathlib import Path

import pytest
from test_automatic_planning import response
from test_period_rule_constraints import planner_with

from knowledgebase.schemas.options import PlanningOptions
from knowledgebase.providers.llm import LLMClient
from knowledgebase.rag.generation import INSUFFICIENT_EVIDENCE, generate_answer
from knowledgebase.schemas import PlannedEvidence
from knowledgebase.rag.hops import HopController
from knowledgebase.rag.planning import PreparedPlanning, RequestControl

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "evals/library-runs/20260928-period-rule-acceptance"
CASE = ROOT / "evals/check-runs/20260928-planner-fact-scope/frozen-case.json"


def replay_scope(*, annotated):
    """Annotated provider outputs are desired decisions, not live measurements."""
    fixture = json.loads(CASE.read_text())
    original = json.loads((ROOT / fixture["source_artifact"]).read_text())
    decision = fixture["expected_decision" if annotated else "original_decision"]
    assessment = fixture["expected_assessment" if annotated else "original_assessment"]
    planner, sdk = planner_with(json.dumps(decision))
    generated = planner.plan(fixture["question"], fixture["question"], lambda: 30)
    evidence = PlannedEvidence.model_validate_json((RUN / "frozen-evidence.json").read_text())
    prepared = PreparedPlanning(generated.plan, evidence.trace.allowed_file_ids, generated.record)
    controller = HopController(
        prepared, None, None, planner, RequestControl(PlanningOptions(), "cl100k_base")
    )
    controller.result = evidence
    controller.result.trace.plan = generated.plan
    controller.result.trace.runs = []
    controller.round_index = 3
    controller.progressed = True
    sdk.responses.create.return_value = response(json.dumps(assessment))
    controller.assess()
    sdk.responses.create.return_value = response(original["answer"])
    answer = generate_answer(
        fixture["question"],
        evidence.evidence.chunks,
        LLMClient(sdk, "offline"),
        assessment=controller.assessment,
    )
    return controller, sdk, answer, fixture


def test_two_missing_facts_abstain_without_the_duplicate_availability_requirement():
    before, before_sdk, before_answer, fixture = replay_scope(annotated=False)
    after, sdk, answer, _ = replay_scope(annotated=True)
    assert len(before.prepared.plan.requirements) == 3
    assert [p["status"] for p in before.assessment["requirements"]] == [
        "missing",
        "missing",
        "supported",
    ]
    assert "ungrouped Pre-Pawn" in before_answer
    assert before_sdk.responses.create.call_count == 3
    assert [r.model_dump() for r in after.prepared.plan.requirements] == fixture[
        "expected_decision"
    ]["requirements"]
    assert after.prepared.plan.answer_rules == before.prepared.plan.answer_rules
    assert after.prepared.plan.original_question == before.prepared.plan.original_question
    assert after.prepared.record["output_text"] == json.dumps(fixture["expected_decision"])
    assert len(after.prepared.plan.queries) == 2
    assert [q.requirement_ids for q in after.prepared.plan.queries] == [["R1"], ["R2"]]
    assert "added_coverage_query" not in after.prepared.record
    assert "ungrouped Handgun" in after.prepared.plan.requirements[0].description
    assert "ungrouped" not in after.prepared.plan.requirements[1].description
    assert "ungrouped" not in after.prepared.plan.queries[1].text
    assert "Pre-Pawn Handgun" in after.prepared.plan.queries[1].text
    assert [p["status"] for p in after.assessment["requirements"]] == ["missing", "missing"]
    assert answer == INSUFFICIENT_EVIDENCE
    assert sdk.responses.create.call_count == 2
    assert all("text" in call.kwargs for call in sdk.responses.create.call_args_list)
    assert after.assessment["context"] == before.assessment["context"]
    assert after.assessment["evidence_catalog"] == before.assessment["evidence_catalog"]
    assert after.trace["stop_reason"] == before.trace["stop_reason"] == "round_limit"
    # Verify production payloads; this does not establish model compliance.
    assert after.prepared.record["prompt_version"] == "dependent-planner-v8"
    assert (
        "not another requested fact or retrieval target"
        in after.prepared.record["input"][0]["content"]
    )
    generation = before_sdk.responses.create.call_args.kwargs["input"]
    assert fixture["question"] in generation[0]["content"]
    assert "use the user's original column names" in generation[1]["content"]


@pytest.mark.parametrize("identity", ["original-rule", "paraphrased-rule", "factual-condition"])
def test_accepted_fact_plans_and_explicit_document_explanation_question_are_preserved(identity):
    row = json.loads((RUN / (identity + ".json")).read_text())
    planner, sdk = planner_with(row["planner_record"]["output_text"])
    generated = planner.plan(row["case"]["question"], row["case"]["question"], lambda: 30)
    assert [r.model_dump() for r in generated.plan.requirements] == row["plan"]["requirements"]
    assert generated.plan.answer_rules == row["plan"]["answer_rules"]
    assert generated.record["output_text"] == row["planner_record"]["output_text"]
    if identity == "factual-condition":
        assert len(generated.plan.requirements) == 3
        assert "explains why" in generated.plan.requirements[2].description
        assert generated.plan.answer_rules == []
    sdk.responses.create.assert_called_once()
