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


def test_review_quotes_offsets_metrics_and_frozen_timing():
    directory=run.DIR
    if not (directory/'acceptance.json').exists():
        pytest.skip('Manual review not recorded yet.')
    from datetime import datetime
    meta=json.loads((directory/'run.json').read_text())
    assert datetime.fromisoformat(run.inputs()['frozen_at']) < datetime.fromisoformat(meta['started_at'])
    answers={a['case_id']:a for a in read_jsonl(directory/'answers.jsonl')}
    reviews=json.loads((directory/'manual-review.json').read_text())
    for review in reviews:
        a=answers[review['case_id']]
        assert digest(a['answer'].encode())==review['answer_sha256']
        assert len(review['points'])==len(review['original_rubric_points'])
        for claim in review['claims']:
            assert claim['answer_quote'] in a['answer']
            for evidence in claim['evidence']:
                source=next(s for s in a['sources'] if s['source_id']==evidence['source_id'])
                assert source['file_name']==evidence['file_name']
                assert source['text'][evidence['start_offset']-source['start_offset']:evidence['end_offset']-source['start_offset']]==evidence['quote']
    # An annotation change must not turn the remaining source failure into a pass.
    acceptance=json.loads((directory/'acceptance.json').read_text())
    assert acceptance['status']=='failed'
    assert acceptance['gates']['named_source_scope'] is False
    assert acceptance['cases_passed']==sum(r['pass'] for r in reviews)==4
    for name in ('before-metrics.json','after-metrics.json'):
        m=json.loads((directory/name).read_text())['metrics']
        prior=json.loads((run.BASE/'after-metrics.json').read_text())['metrics']
        assert set(prior)<=set(m)
        for key in ('recall_at_k','precision_at_k','hit_rate_at_k','mrr_at_k','ndcg_at_k','full_evidence_recall'):
            assert m[key]['origin'].startswith('Inherited')
        assert m['total_seconds']['status']=='not_applicable'
        assert m['answer_correctness']['status']=='measured'


def test_report_and_status_document_links():
    import re
    from pathlib import Path
    paths=[run.DIR/'README.md',run.DIR/'REVIEW.md',run.DIR/'PLAN.md',
           Path('README.md'),Path('docs/answer-grounding.md'),Path('docs/v1/README.md'),Path('docs/v1/merge-readiness.md')]
    for path in paths:
        text=path.read_text()
        assert not re.search(r'[\u4e00-\u9fff]',text)
        for target in re.findall(r'\]\(([^\s)]+)\)',text):
            if '://' in target or target.startswith(('#','mailto:')):
                continue
            assert (path.parent/target.split('#')[0]).exists(), (path,target)
