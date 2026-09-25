"""Verify the bounded prompt comparison and explicit annotation correction."""
import importlib
import json
from copy import deepcopy

import pytest
from evals.evaluate import digest, read_jsonl

run = importlib.import_module('evals.library-runs.20260925-answer-focus.run')


def test_comparison_changes_only_instructions():
    frozen = run.inputs()
    prior = json.loads((run.BASE / 'freeze.json').read_text())['config']
    assert frozen['config'] == {**prior, 'answer_reasoning_effort': None}
    calls = [c for c in read_jsonl(run.BASE / 'calls.jsonl') if c['stage'] == 'generation']
    assert len(calls) == len(run.IDS) == 5
    for call in calls:
        original = deepcopy(call)
        messages = run.messages_for(call)
        assert messages[0] == call['messages'][0]
        assert messages[1]['role'] == call['messages'][1]['role'] == 'developer'
        assert messages[1]['content'] != call['messages'][1]['content']
        assert call == original


def test_annotation_change_is_limited_and_original_is_retained():
    original = json.loads((run.DIR / 'original-cases.json').read_text())
    assert original == json.loads((run.BASE / 'cases.json').read_text())
    revised = json.loads((run.DIR / 'cases.json').read_text())
    differences = []
    for before, after in zip(original, revised, strict=True):
        for key in before:
            if before[key] != after[key]:
                differences.append((before['id'], key))
        if before['id'] == 'accept-awards-jobs':
            assert before['expected_answer_points'][1] == after['expected_answer_points'][1]
    assert differences == [('accept-awards-jobs', 'expected_answer_points')]


def test_completed_replay_preserves_sources_and_deltas():
    if not (run.DIR / 'answers.jsonl').exists():
        pytest.skip('Preflight: no provider calls yet.')
    baseline = {a['case_id']: a for a in read_jsonl(run.BASE / 'answers.jsonl')}
    answers = read_jsonl(run.DIR / 'answers.jsonl')
    calls = read_jsonl(run.DIR / 'calls.jsonl')
    assert [a['case_id'] for a in answers] == [c['case_id'] for c in calls] == run.IDS
    for row, call in zip(answers, calls, strict=True):
        assert call['reasoning'] is None
        assert call['model'] == 'gpt-4.1'
        assert row['sources'] == baseline[row['case_id']]['sources']
        assert row['retrieval'] == baseline[row['case_id']]['retrieval']
        assert row['answer'] == ''.join(d['delta'] for d in call['deltas'])
        assert digest(call['messages'][1]['content'].encode()) == run.inputs()['prompt_sha256']
        assert 'total_seconds' not in row
