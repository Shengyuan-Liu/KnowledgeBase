"""Keep answering instructions outside source-verifiable plan requirements."""
import json
from pathlib import Path
from unittest.mock import Mock

from knowledgebase.config import PlanningOptions
from knowledgebase.providers.planner import PlannerClient
from knowledgebase.rag.generation import _answer_messages
from knowledgebase.schemas import (
    PlanDecision, RetrievalPlan, PlannedEvidence,
)
from knowledgebase.services.hops import HopController
from knowledgebase.services.planning import PreparedPlanning, RequestControl
from test_automatic_planning import DIRECT, response

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / 'evals/check-runs/20260927-answer-rules/frozen-case.json'


def replay_controller(*, separated):
    """Replay annotated provider outputs; this does not test model classification."""
    fixture = json.loads(CASE.read_text())
    raw = json.loads((ROOT / fixture['source_artifact']).read_text())
    saved = raw['answer']['retrieval']['planning']
    decision = fixture['expected_decision' if separated else 'original_decision']
    assessment = fixture['expected_assessment' if separated else 'original_assessment']
    sdk = Mock()
    sdk.with_options.return_value = sdk
    sdk.responses.create.side_effect = [response(json.dumps(decision)), response(json.dumps(assessment))]
    planner = PlannerClient(sdk, 'offline', PlanningOptions(), 'cl100k_base')
    generated = planner.plan(fixture['question'], fixture['question'], lambda: 30)
    prepared = PreparedPlanning(generated.plan, saved['trace']['allowed_file_ids'], generated.record)
    controller = HopController(prepared, Mock(), Mock(), Mock(), planner,
                               RequestControl(PlanningOptions(), 'cl100k_base'))
    controller.result = PlannedEvidence.model_validate(saved['hops']['rounds'][0])
    controller.result.trace.plan = generated.plan
    controller.round_index = 1
    controller.progressed = True
    controller.assess()
    return controller, sdk, fixture


def test_recorded_rule_is_retained_without_a_false_missing_point_or_gap_search():
    before, old_sdk, fixture = replay_controller(separated=False)
    assert before.trace['stop_reason'] == 'no_eligible_query'
    assert before.assessment['requirements'][-1]['status'] == 'missing'
    after, sdk, _ = replay_controller(separated=True)
    plan = after.prepared.plan
    assert after.trace['stop_reason'] == 'requirements_supported'
    assert [r.requirement_id for r in plan.requirements] == ['R1', 'R2', 'R3', 'R4']
    assert plan.answer_rules == [fixture['classification_annotation']['rule_text']]
    assert len(plan.queries) == 4 and 'added_coverage_query' not in after.prepared.record
    assert all(q.requirement_ids == [f'R{i}'] for i, q in enumerate(plan.queries, 1))
    assert [r['status'] for r in after.assessment['requirements']] == ['supported'] * 4
    assert after.supplements == [] and after.trace['supplementary_queries'] == []
    assert sdk.responses.create.call_count == old_sdk.responses.create.call_count == 2
    assert after.assessment['context'] == before.assessment['context']
    assert after.assessment['evidence_catalog'] == before.assessment['evidence_catalog']
    for old, new in zip(before.assessment['requirements'][:4], after.assessment['requirements'], strict=True):
        assert old == new
    assessment_payload = json.loads(sdk.responses.create.call_args.kwargs['input'][-1]['content'])
    assert 'answer_rules' not in assessment_payload
    assert len(assessment_payload['requirements']) == 4
    assert after.assessment['record']['prompt_version'] == 'evidence-sufficiency-v6'
    # Original user guidance still reaches generation as the original question.
    messages = _answer_messages(fixture['question'], after.result.evidence.chunks, assessment=after.assessment)
    assert fixture['question'] in messages[0]['content']
    assert plan.answer_rules[0] in messages[0]['content']
    assert RetrievalPlan.model_validate_json(plan.model_dump_json()).answer_rules == plan.answer_rules


def test_old_plans_are_not_silently_reclassified_or_rewritten():
    fixture = json.loads(CASE.read_text())
    old = PlanDecision.model_validate(fixture['original_decision']).to_plan(fixture['question'], fixture['question'])
    assert old.answer_rules == []
    assert old.requirements[-1].requirement_id == 'R5'
    assert len(old.requirements) == 5


def test_direct_rule_is_preserved_without_inventing_a_requirement():
    rule = 'If the source does not say, state that limitation.'
    plan = PlanDecision(**{**DIRECT, 'answer_rules': [rule]}).to_plan('Original', 'Resolved')
    assert len(plan.requirements) == len(plan.queries) == 1
    assert plan.answer_rules == [rule]
    assert plan.queries[0].text == 'Resolved'


def test_fact_condition_stays_a_requirement_not_a_text_pattern_filter():
    question = 'If revenue fell, what caused the decline?'
    value = {'route': 'decomposed', 'answer_rules': [], 'dependencies': [],
             'requirements': [{'requirement_id': 'trend', 'description': 'Whether revenue fell'},
                              {'requirement_id': 'reason', 'description': question}],
             'queries': [{'query_id': 'q1', 'text': question, 'requirement_ids': ['trend', 'reason']}]}
    plan = PlanDecision(**value).to_plan(question, question)
    assert [r.description for r in plan.requirements] == ['Whether revenue fell', question]
    assert plan.answer_rules == []
