"""Verify saved-source isolation before paid replay and artifact fidelity afterward."""
import importlib
import json
from copy import deepcopy

from evals.evaluate import digest, read_jsonl

run = importlib.import_module('evals.library-runs.20260925-grounding-order.run')


def test_frozen_replay_changes_only_developer_instructions():
    frozen = run.inputs()
    calls = [c for c in read_jsonl(run.BASE / 'calls.jsonl') if c.get('case_id') in run.IDS and c['stage'] == 'generation']
    assert len(calls) == len(run.IDS) == 5
    assert frozen['case_ids'] == run.IDS
    for call in calls:
        original = deepcopy(call)
        messages = run.messages_for(call)
        assert messages == list(reversed(call['messages']))
        assert messages[1]['content'] == call['messages'][0]['content']
        assert call == original
    cases = json.loads((run.DIR / 'cases.json').read_text())
    assert cases == [c for c in json.loads((run.BASE / 'cases.json').read_text()) if c['id'] in run.IDS]
    assert sum(not c['answerable'] for c in cases) == 2


def test_completed_replay_preserves_sources_and_all_deltas():
    if not (run.DIR / 'answers.jsonl').exists():
        import pytest
        pytest.skip('Preflight: live results do not exist yet.')
    baseline = {a['case_id']: a for a in read_jsonl(run.BASE / 'answers.jsonl')}
    answers = read_jsonl(run.DIR / 'answers.jsonl')
    calls = read_jsonl(run.DIR / 'calls.jsonl')
    assert [a['case_id'] for a in answers] == [c['case_id'] for c in calls] == run.IDS
    for row, call in zip(answers, calls, strict=True):
        assert row['sources'] == baseline[row['case_id']]['sources']
        assert row['retrieval'] == baseline[row['case_id']]['retrieval']
        assert row['answer'] == ''.join(d['delta'] for d in call['deltas'])
        assert digest(call['messages'][1]['content'].encode()) == run.inputs()['prompt_sha256']
        assert 'total_seconds' not in row  # No inherited service latency as a fresh measurement.
