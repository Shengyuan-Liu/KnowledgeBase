"""Verify saved-source isolation before paid replay and artifact fidelity afterward."""
import importlib
import json
from copy import deepcopy

from evals.evaluate import digest, read_jsonl

run = importlib.import_module('evals.library-runs.20260925-source-scope.run')


def test_frozen_replay_changes_only_developer_instructions():
    frozen = run.inputs()
    calls = [c for c in read_jsonl(run.BASE / 'calls.jsonl') if c.get('case_id') in run.IDS and c['stage'] == 'generation']
    assert len(calls) == len(run.IDS) == 5
    assert frozen['case_ids'] == run.IDS
    for call in calls:
        original = deepcopy(call)
        messages = run.messages_for(call)
        assert messages[1:] == call['messages'][1:]
        assert messages[0]['content'] != call['messages'][0]['content']
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
        assert digest(call['messages'][0]['content'].encode()) == run.inputs()['prompt_sha256']
        assert 'total_seconds' not in row  # No inherited service latency as a fresh measurement.


def test_review_quotes_offsets_and_failure_disclosure():
    answers = {a['case_id']:a for a in read_jsonl(run.DIR/'answers.jsonl')}
    reviews = json.loads((run.DIR/'manual-review.json').read_text())
    assert {r['case_id'] for r in reviews} == set(run.IDS)
    for review in reviews:
        answer = answers[review['case_id']]
        assert review['answer_sha256'] == digest(answer['answer'].encode())
        for claim in review['claims']:
            assert claim['answer_quote'] in answer['answer']
            for evidence in claim['evidence']:
                source = next(s for s in answer['sources'] if s['source_id']==evidence['source_id'])
                assert source['text'][evidence['start_offset']-source['start_offset']:evidence['end_offset']-source['start_offset']] == evidence['quote']
    result = json.loads((run.DIR/'acceptance.json').read_text())
    assert result['status'] == 'failed'
    assert result['cases_passed'] == sum(r['pass'] for r in reviews) == 3
    assert not result['gates']['associated_citation_support']
    assert json.loads((run.BASE/'acceptance.json').read_text())['cases_passed'] == 7


def test_complete_measurement_inventory_and_generation_scope():
    baseline = json.loads((run.BASE/'qualified-metrics.json').read_text())['metrics']
    current = json.loads((run.DIR/'after-metrics.json').read_text())['metrics']
    assert set(baseline) <= set(current)
    def inspect(entry):
        if 'status' in entry:
            assert entry['status'] in ('measured','not_applicable','unavailable')
            if entry['status']=='measured':
                assert all(k in entry for k in ('value','unit','n','method','artifact'))
            else:
                assert entry['value'] is None and entry['reason']
        else:
            for child in entry.values(): inspect(child)
    for entry in current.values(): inspect(entry)
    for key in ('total_seconds','first_delta_seconds','retrieval_seconds','ingestion'):
        assert current[key]['status']=='not_applicable'
    assert current['cost']['status']=='unavailable'
    assert current['generation_seconds']['n']==5
    assert current['token_usage']['generation']['n']==5


def test_document_links_and_english_artifact_text():
    from pathlib import Path
    import re
    docs = [Path('README.md'), Path('docs/v1/README.md'), Path('docs/v1/merge-readiness.md'),
            Path('docs/answer-grounding.md'), run.DIR/'README.md', run.DIR/'PLAN.md',
            Path('evals/check-runs/20260925-source-scope/README.md')]
    for path in docs:
        text=path.read_text()
        assert not re.search(r'[\u4e00-\u9fff]',text)
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text):
            if '://' not in target and not target.startswith('#'):
                assert (path.parent/target.split('#')[0]).exists(), (path,target)
        assert text.endswith('\n')
