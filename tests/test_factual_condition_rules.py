"""Replay the observed rule duplication with explicit, offline classification controls."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from test_automatic_planning import response
from test_period_rule_constraints import planner_with

from knowledgebase.config import PlanningOptions
from knowledgebase.providers.llm import LLMClient
from knowledgebase.rag.generation import _answer_messages, generate_answer
from knowledgebase.schemas import (
    PlannedEvidence,
    RetrievalPlan,
)
from knowledgebase.services.hops import HopController
from knowledgebase.services.planning import PreparedPlanning, RequestControl

PROJECT = Path(__file__).resolve().parents[1]
FIXTURE = PROJECT / "evals/check-runs/20260929-factual-condition-rules/frozen-cases.json"
BASE = PROJECT / "evals/library-runs/20260929-planner-dependency-acceptance"


def recorded(identity):
    fixture = json.loads(FIXTURE.read_text())
    item = next(row for row in fixture["rows"] if row["case_id"] == identity)
    return json.loads((PROJECT / item["source_artifact"]).read_text()), item["expected_decision"]


def replay_case(identity, *, annotated):
    """Use controlled model outputs; this does not measure model compliance."""
    saved, expected = recorded(identity)
    output = json.dumps(expected) if annotated else saved["planner_record"]["output_text"]
    planner, sdk = planner_with(output)
    sdk.responses.create.side_effect = [
        response(output),
        response(saved["assessment"]["record"]["output_text"]),
        response(saved["answer"]),
    ]
    question = saved["case"]["question"]
    generated = planner.plan(question, question, lambda: 30)
    evidence = PlannedEvidence.model_validate_json((BASE / "frozen-evidence.json").read_text())
    prepared = PreparedPlanning(generated.plan, evidence.trace.allowed_file_ids, generated.record)
    controller = HopController(
        prepared, None, None, planner, RequestControl(PlanningOptions(), "cl100k_base")
    )
    controller.result = evidence
    controller.result.trace.plan = generated.plan
    controller.result.trace.runs = []
    controller.round_index = 3
    controller.progressed = True
    controller.assess()
    answer = generate_answer(
        question,
        evidence.evidence.chunks,
        LLMClient(sdk, "offline"),
        assessment=controller.assessment,
    )
    return generated, controller, sdk, answer


def test_recorded_duplicate_is_a_semantic_error_not_an_invented_quote_or_repaired_output():
    saved, _ = recorded("factual-condition")
    result, _, sdk, _ = replay_case("factual-condition", annotated=False)
    assert result.plan.answer_rules == saved["plan"]["answer_rules"]
    assert result.plan.answer_rules
    assert all(rule in saved["case"]["question"] for rule in result.plan.answer_rules)
    assert result.record["output_text"] == saved["planner_record"]["output_text"]
    assert (
        RetrievalPlan.model_validate_json(result.plan.model_dump_json()).answer_rules
        == result.plan.answer_rules
    )
    assert sdk.responses.create.call_count == 3
    assert all(c.kwargs["max_retries"] == 0 for c in sdk.with_options.call_args_list)


def test_empty_rule_annotation_preserves_factual_condition_and_downstream_requests():
    saved, expected = recorded("factual-condition")
    before, before_controller, before_sdk, before_answer = replay_case(
        "factual-condition", annotated=False
    )
    after, controller, sdk, answer = replay_case("factual-condition", annotated=True)
    assert after.plan.answer_rules == []
    assert after.plan.route == "decomposed" and after.plan.dependencies == []
    assert after.plan.requirements == before.plan.requirements and len(after.plan.requirements) == 3
    assert after.plan.queries == before.plan.queries and len(after.plan.queries) == 3
    assert after.plan.model_dump(exclude={"answer_rules"}) == before.plan.model_dump(
        exclude={"answer_rules"}
    )
    assert after.record["output_text"] == json.dumps(expected)
    assert "added_coverage_query" not in after.record
    assert {k: v for k, v in controller.assessment.items() if k != "record"} == {
        k: v for k, v in before_controller.assessment.items() if k != "record"
    }
    assert [r["status"] for r in controller.assessment["requirements"]] == [
        "supported",
        "supported",
        "missing",
    ]
    assert (
        controller.trace["stop_reason"] == before_controller.trace["stop_reason"] == "round_limit"
    )
    assert sdk.responses.create.call_count == before_sdk.responses.create.call_count == 3
    for index in [1, 2]:
        assert (
            sdk.responses.create.call_args_list[index].kwargs
            == before_sdk.responses.create.call_args_list[index].kwargs
        )
    generation = sdk.responses.create.call_args_list[2].kwargs["input"]
    assert saved["case"]["question"] in generation[0]["content"]
    assert (
        before.plan.answer_rules[0] in generation[0]["content"]
    )  # Preserved inside the original question.
    assert answer == before_answer == saved["answer"]  # Frozen mock answer, not new model quality.
    assert after.record["prompt_version"] == "dependent-planner-v8"
    assert "This example has answer_rules: []" in after.record["input"][0]["content"]


@pytest.mark.parametrize("identity", ["original-rule", "paraphrased-rule", "missing-year"])
def test_observed_real_answering_rules_and_column_scopes_remain_preserved(identity):
    saved, expected = recorded(identity)
    result, _, sdk, answer = replay_case(identity, annotated=True)
    assert result.plan.answer_rules == saved["case"]["expected_answer_rules"]
    assert [r.model_dump() for r in result.plan.requirements] == expected["requirements"]
    assert [q.model_dump(exclude={"file_ids"}) for q in result.plan.queries] == expected["queries"]
    assert answer == saved["answer"]
    assert sdk.responses.create.call_count == (2 if identity == "missing-year" else 3)
    if identity == "missing-year":
        assert "ungrouped" not in result.plan.queries[1].text
        assert "Pre-Pawn Handgun" in result.plan.queries[1].text
        assert all("November 2016" in q.text for q in result.plan.queries)


def test_mixed_fact_condition_and_real_answering_instruction_keep_only_the_instruction():
    saved, expected = recorded("factual-condition")
    instruction_case, _ = recorded("original-rule")
    rule = instruction_case["case"]["expected_answer_rules"][0]
    question = saved["case"]["question"] + " " + rule
    decision = deepcopy(expected)
    decision["answer_rules"] = [rule]
    planner, sdk = planner_with(json.dumps(decision))
    result = planner.plan(question, question, lambda: 30)
    assert result.plan.answer_rules == [rule]
    assert len(result.plan.requirements) == len(result.plan.queries) == 3
    assert [r.model_dump() for r in result.plan.requirements] == expected["requirements"]
    assert result.plan.original_question == question
    evidence = PlannedEvidence.model_validate_json((BASE / "frozen-evidence.json").read_text())
    messages = _answer_messages(question, evidence.evidence.chunks, assessment=saved["assessment"])
    assert question in messages[0]["content"]
    sdk.responses.create.assert_called_once()
