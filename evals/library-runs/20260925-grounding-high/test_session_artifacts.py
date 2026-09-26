"""Audit every retained attempt, source quote and metric in this correction session."""
import json
from pathlib import Path
import re
from statistics import mean

import pytest
from evals.evaluate import digest, read_jsonl

ROOT = Path(__file__).parent.parent
NAMES = ['20260925-source-attribution', '20260925-grounding-order',
         '20260925-grounding-model', '20260925-grounding-reasoning', '20260925-grounding-high']


@pytest.mark.parametrize('name', NAMES)
def test_raw_observations_review_and_inventory(name):
    path = ROOT/name
    frozen=json.loads((path/'freeze.json').read_text())
    meta=json.loads((path/'run.json').read_text())
    assert frozen['frozen_at'] < meta['started_at']
    assert digest((path/'PLAN.md').read_bytes()) == frozen['plan_sha256']
    baseline=Path(meta['baseline'])
    for filename, checksum in frozen['baseline_files'].items():
        assert digest((baseline/filename).read_bytes()) == checksum
    calls=read_jsonl(path/'calls.jsonl');answers=read_jsonl(path/'answers.jsonl')
    original={a['case_id']:a for a in read_jsonl(ROOT/'20260925-v1-codex-acceptance/answers.jsonl')}
    original_calls={c['case_id']:c for c in read_jsonl(ROOT/'20260925-v1-codex-acceptance/calls.jsonl') if c['stage']=='generation'}
    assert [a['case_id'] for a in answers] == [c['case_id'] for c in calls] == frozen['case_ids']
    for answer, call in zip(answers,calls,strict=True):
        assert answer['answer'] == ''.join(d['delta'] for d in call['deltas'])
        assert answer['sources'] == original[answer['case_id']]['sources']
        user=next(m for m in call['messages'] if m['role']=='user')
        assert user == next(m for m in original_calls[answer['case_id']]['messages'] if m['role']=='user')
        developer=next(m for m in call['messages'] if m['role']=='developer')
        assert digest(developer['content'].encode()) == frozen['prompt_sha256']
        expected_effort=frozen['config'].get('answer_reasoning_effort')
        assert call.get('reasoning') == ({'effort':expected_effort} if expected_effort else None)
        assert call['model'] == frozen['config']['answer_model']
        assert 'api_key' not in call
        assert 'total_seconds' not in answer
    filename='qualified-manual-review.json' if name=='20260925-source-attribution' else 'manual-review.json'
    reviews=json.loads((path/filename).read_text())
    by={a['case_id']:a for a in answers}
    assert {r['case_id'] for r in reviews} == set(by)
    for review in reviews:
        answer=by[review['case_id']]
        assert digest(answer['answer'].encode()) == review['answer_sha256']
        for claim in review['claims']:
            assert claim['answer_quote'] in answer['answer']
            for evidence in claim['evidence']:
                source=next(s for s in answer['sources'] if s['source_id']==evidence['source_id'])
                assert source['text'][evidence['start_offset']-source['start_offset']:evidence['end_offset']-source['start_offset']] == evidence['quote']
    result=json.loads((path/'acceptance.json').read_text())
    assert result['cases_passed']==sum(r['pass'] for r in reviews)
    assert (result['status']=='passed') == all(result['gates'].values())
    scored=json.loads((path/'after-metrics.json').read_text())['metrics']
    inventory=json.loads((ROOT/'20260925-v1-codex-acceptance/qualified-metrics.json').read_text())['metrics']
    assert set(inventory) <= set(scored)
    points=[p for r in reviews for p in r['points']]
    assert scored['answer_correctness']['value']==mean(p['correctness']/2 for p in points)
    def inspect(entry):
        if 'status' in entry:
            assert entry['status'] in ('measured','not_applicable','unavailable')
            if entry['status']=='measured':
                assert all(k in entry for k in ('value','unit','n','method','artifact'))
            else:assert entry['value'] is None and entry['reason']
        else:
            for child in entry.values():inspect(child)
    for entry in scored.values():inspect(entry)
    assert scored['cost']['status']=='unavailable'
    for key in ('total_seconds','first_delta_seconds','retrieval_seconds','ingestion'):
        assert scored[key]['status']=='not_applicable'


def test_session_document_links_and_format():
    paths=[Path('README.md'),Path('docs/v1/README.md'),Path('docs/v1/merge-readiness.md'),
           Path('docs/answer-grounding.md'),Path('docs/configuration.md')]
    for name in NAMES:
        paths += [ROOT/name/'README.md', ROOT/name/'PLAN.md',Path('evals/check-runs')/name/'README.md']
    for path in paths:
        text=path.read_text()
        assert text.endswith('\n')
        assert not re.search(r'[\u4e00-\u9fff]',text)
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text):
            if '://' not in target and not target.startswith('#'):
                assert (path.parent/target.split('#')[0]).exists(), (path,target)
