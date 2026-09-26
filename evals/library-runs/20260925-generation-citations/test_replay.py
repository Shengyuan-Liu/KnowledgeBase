"""Offline checks for a paid replay's fixed-input and measurement boundaries."""
import importlib.util
import json
from pathlib import Path

from evals.evaluate import digest, read_jsonl
from knowledgebase.rag.generation import ANSWER_INSTRUCTIONS

spec = importlib.util.spec_from_file_location('citation_replay', Path(__file__).with_name('run_replay.py'))
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


def test_only_developer_instructions_change_in_all_frozen_requests():
    frozen, cases, answers = replay.inputs()
    calls = [c for c in read_jsonl(replay.BASELINE / 'calls.jsonl') if c['stage'] == 'generation']
    assert len(calls) == len(cases) == len(answers) == 24
    assert {c['case_id'] for c in calls} == {c['id'] for c in cases}
    for call in calls:
        before = json.dumps(call, sort_keys=True)
        messages = replay.messages_for(call)
        assert messages[1:] == call['messages'][1:]
        assert messages[0] == {'role': 'developer', 'content': ANSWER_INSTRUCTIONS}
        assert messages[0] != call['messages'][0]
        assert json.dumps(call, sort_keys=True) == before
    assert frozen['config']['answer_model'] == calls[0]['model']


def test_baseline_reviews_match_exact_answers_and_frozen_protocol():
    frozen, _, answers = replay.inputs()
    reviews = read_jsonl(replay.BASELINE / 'reviews.jsonl')
    by_id = {a['case_id']: a for a in answers}
    assert len(reviews) == len(answers)
    for review in reviews:
        assert review['status'] == 'ok'
        assert review['protocol_sha256'] == frozen['judge_protocol_sha256']
        assert review['model'] == frozen['config']['judge_model']
        assert review['reasoning_effort'] == frozen['config']['judge_reasoning_effort']
        assert review['answer_sha256'] == digest(json.dumps(by_id[review['case_id']], sort_keys=True).encode())


def test_replay_keeps_evidence_and_removes_unmeasured_service_timings():
    _, _, answers = replay.inputs()
    for original in answers:
        row = replay.replay_row(original)
        for key in ('sources', 'coverage', 'ranking', 'retrieval'):
            assert row[key] == original[key]
        for key in replay.STAGES_NOT_RUN:
            assert row[key] is None
        assert row['generation_seconds'] == original['generation_seconds']
        assert 'events' not in row and 'conversation_id' not in row
