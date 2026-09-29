"""Replay observed rule invention and period failures without live model calls."""
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from knowledgebase.config import PlanningOptions
from knowledgebase.providers.llm import LLMClient
from knowledgebase.providers.planner import PlannerClient
from knowledgebase.rag.generation import INSUFFICIENT_EVIDENCE, generate_answer
from knowledgebase.rag.planned_retrieval import PlannedEvidence
from knowledgebase.services.hops import HopController
from knowledgebase.services.planning import PreparedPlanning, RequestControl
from test_automatic_planning import response

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "evals/library-runs/20260928-answer-rules-acceptance"


def recorded(identity):
    return json.loads((FROZEN / (identity + ".json")).read_text())


def planner_with(output):
    sdk = Mock()
    sdk.with_options.return_value = sdk
    sdk.responses.create.return_value = response(output)
    return PlannerClient(sdk, "offline", PlanningOptions(), "cl100k_base"), sdk


def test_observed_invented_rule_is_rejected_without_repair_or_retry():
    row = recorded("factual-condition")
    planner, sdk = planner_with(row["planner_record"]["output_text"])
    with pytest.raises(ValueError, match="quote the original question exactly"):
        planner.plan(row["case"]["question"], row["case"]["question"], lambda: 30)
    assert sdk.responses.create.call_count == 1
    assert sdk.with_options.call_args.kwargs["max_retries"] == 0
    assert row["plan"]["answer_rules"]  # Historical failure remains untouched.


@pytest.mark.parametrize("identity", ["original-rule", "paraphrased-rule", "missing-year"])
def test_observed_user_rules_are_accepted_verbatim_with_fact_dimensions_preserved(identity):
    row = recorded(identity)
    planner, sdk = planner_with(row["planner_record"]["output_text"])
    result = planner.plan(row["case"]["question"], row["case"]["question"], lambda: 30)
    assert result.plan.answer_rules == row["plan"]["answer_rules"]
    assert [r.model_dump() for r in result.plan.requirements] == row["plan"]["requirements"]
    assert result.record["output_text"] == row["planner_record"]["output_text"]
    assert result.record["prompt_version"] == "dependent-planner-v8"
    sdk.responses.create.assert_called_once()


def test_factual_condition_can_keep_its_requirements_with_no_invented_rule():
    row = recorded("factual-condition")
    annotated = json.loads(row["planner_record"]["output_text"])
    annotated["answer_rules"] = []
    planner, _ = planner_with(json.dumps(annotated))
    result = planner.plan(row["case"]["question"], row["case"]["question"], lambda: 30)
    assert result.plan.answer_rules == []
    assert [r.model_dump() for r in result.plan.requirements] == row["plan"]["requirements"]
    assert len(result.plan.requirements) == 3


def replay_period(*, annotated):
    """Annotation supplies the desired missing decision; no model accuracy claim."""
    row = recorded("missing-year")
    planner, sdk = planner_with(row["planner_record"]["output_text"])
    generated = planner.plan(row["case"]["question"], row["case"]["question"], lambda: 30)
    decision = json.loads(row["assessment"]["record"]["output_text"])
    if annotated:
        for point in decision["requirements"]:
            point.update(status="missing", gap="The supplied values are for November 2015; the requested November 2016 values are not supplied.", references=[])
    sdk.responses.create.return_value = response(json.dumps(decision))
    evidence = PlannedEvidence.model_validate_json((FROZEN / "frozen-evidence.json").read_text())
    prepared = PreparedPlanning(generated.plan, evidence.trace.allowed_file_ids, generated.record)
    controller = HopController(prepared, None, None, None, planner, RequestControl(PlanningOptions(), "cl100k_base"))
    controller.result = evidence
    controller.result.trace.plan = generated.plan
    controller.result.trace.runs = []
    controller.round_index = 3
    controller.progressed = True
    controller.assess()
    # Capture the production assessment request before the optional generation call.
    assessment_request = sdk.responses.create.call_args.kwargs
    sdk.responses.create.return_value = response(row["answer"])
    answer = generate_answer(row["case"]["question"], evidence.evidence.chunks,
        LLMClient(sdk, "offline"), assessment=controller.assessment)
    return controller, sdk, assessment_request, answer


def test_period_mismatch_annotation_abstains_while_raw_bad_semantics_are_not_silently_repaired():
    before, before_sdk, _, before_answer = replay_period(annotated=False)
    after, after_sdk, payload, after_answer = replay_period(annotated=True)
    assert before_answer == recorded("missing-year")["answer"]
    assert before.trace["stop_reason"] == "requirements_supported"
    assert before_sdk.responses.create.call_count == 3
    assert after_answer == INSUFFICIENT_EVIDENCE
    assert after.trace["stop_reason"] == "round_limit"
    assert after_sdk.responses.create.call_count == 2  # No generation on all-missing.
    assert [p["status"] for p in after.assessment["requirements"]] == ["missing", "missing"]
    assert before.assessment["context"] == after.assessment["context"]
    assert before.assessment["evidence_catalog"] == after.assessment["evidence_catalog"]
    assert "November - 2015" in after.assessment["context"]
    request = json.loads(payload["input"][-1]["content"])
    assert "November 2016" in request["original_question"]
    assert "[p2] November - 2015" in request["context"]
    assert "requested-period value is missing" in payload["input"][0]["content"]
    assert after.assessment["record"]["prompt_version"] == "evidence-sufficiency-v5"
    generation = before_sdk.responses.create.call_args.kwargs["input"]
    assert "November 2016" in generation[0]["content"] and "November - 2015" in generation[0]["content"]
    assert "even if an assessment calls" in generation[1]["content"]
