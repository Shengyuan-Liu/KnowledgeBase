"""Validate frozen source scope before calls and raw acceptance artifacts later."""
import importlib
import json
from pathlib import Path

import pytest
from evals.evaluate import read_jsonl
from knowledgebase.rag.scope import document_references,identity_labels,resolve_document_scope
from knowledgebase.schemas import ScopeFile
run=importlib.import_module('evals.library-runs.20260925-document-representation.run')


def test_frozen_sources_annotations_and_configuration():
    frozen,cases,docs=run.inputs()
    assert len(cases)==11 and len(docs)==17
    assert frozen['config']['answer_model']=='gpt-4.1'
    assert frozen['config']['answer_reasoning_effort'] is None
    originals=json.loads((run.DIR/'original-cases.json').read_text())
    assert [c['question'] for c in cases[:8]]==[c['question'] for c in originals]
    assert sum(c['answerable'] for c in cases)==7


def test_real_corpus_references_resolve_without_guessing_or_provider_calls():
    _,cases,docs=run.inputs()
    catalog=[ScopeFile(file_id=name,file_name=name,labels=identity_labels(name,text)) for name,text in docs.items()]
    scopes={c['id']:resolve_document_scope(document_references(c['question']),catalog) for c in cases}
    assert scopes['accept-awards-jobs'].file_ids==['masters-in-data-science-faq-general.txt']
    assert scopes['accept-beta-header-scope'].file_ids==['anthropic_api.md']
    assert set(scopes['scope-compare-faqs'].file_ids)=={'masters-in-data-science-faq-general.txt','masters-in-data-science-faq.txt'}
    assert scopes['scope-ambiguous-faq'].status=='ambiguous'
    assert scopes['scope-missing-file'].status=='not_found'


def test_recorded_run_preserves_successes_and_the_timeout():
    if not (run.DIR/'answers.jsonl').exists():
        pytest.skip('Preflight: no live results yet.')
    rows=read_jsonl(run.DIR/'answers.jsonl');calls=read_jsonl(run.DIR/'calls.jsonl')
    assert len(rows)==11
    for a in rows:
        if a['status'] != 'ok':
            assert a['case_id'] == 'accept-unspecified-api-error'
            assert a['error_type'] == 'APITimeoutError'
            assert a['events'][-1]['event'] == 'error'
            assert not any(e['event'] == 'complete' for e in a['events'])
            assert a['answer'] == ''.join(e['data']['delta'] for e in a['events'] if e['event'] == 'answer_delta')
            assert any(c['case_id'] == a['case_id'] and c['status'] == 'error' for c in calls)
            continue
        assert a['answer']==''.join(e['data']['delta'] for e in a['events'] if e['event']=='answer_delta')
        scope=a['retrieval']['document_scope']
        if scope:
            allowed=set(scope['file_ids'])
            assert {s['file_id'] for s in a['sources']}<=allowed
            assert {c['file_id'] for c in a['retrieval']['candidates']}<=allowed
            if scope['status']!='resolved':
                assert not [c for c in calls if c.get('case_id')==a['case_id']]
                assert not a['sources'] and not a['retrieval']['candidates']
    assert len([c for c in calls if c['stage']=='generation'])==9


RECOVERY = run.DIR.parent / '20260925-scope-timeout-recovery'
BASELINE = run.DIR.parent / '20260925-document-scope'


def test_recovery_uses_identical_model_input_and_product_code():
    before = next(c for c in read_jsonl(run.DIR/'calls.jsonl')
                  if c['stage'] == 'generation' and c['status'] == 'error')
    after = next(c for c in read_jsonl(RECOVERY/'calls.jsonl') if c['stage'] == 'generation')
    for key in ('case_id', 'model', 'messages', 'reasoning'):
        assert before[key] == after[key]
    assert after['status'] == 'ok'
    a = json.loads((run.DIR/'run.json').read_text())
    b = json.loads((RECOVERY/'run.json').read_text())
    assert a['git']['implementation_sha256'] == b['git']['implementation_sha256']
    assert a['index_sha256'] == b['index_sha256']
    assert {k:v for k,v in a['config'].items() if k != 'data_dir'} == {k:v for k,v in b['config'].items() if k != 'data_dir'}
    cases = json.loads((BASELINE/'cases.json').read_text())
    assert cases == json.loads((run.DIR/'cases.json').read_text())
    assert [c for c in cases if c['id'] == before['case_id']] == json.loads((RECOVERY/'cases.json').read_text())
    assert (BASELINE/'chunks.json').read_bytes() == (run.DIR/'chunks.json').read_bytes() == (RECOVERY/'chunks.json').read_bytes()


def test_manual_claim_quotes_and_offsets_match_raw_sources():
    from evals.evaluate import digest
    for directory in (run.DIR, RECOVERY):
        answers = {a['case_id']:a for a in read_jsonl(directory/'answers.jsonl')}
        cases = {c['id']:c for c in json.loads((directory/'cases.json').read_text())}
        for r in json.loads((directory/'manual-review.json').read_text()):
            a = answers[r['case_id']]
            assert r['answer_sha256'] == digest(a['answer'].encode())
            assert [p['reference'] for p in r['points']] == cases[r['case_id']]['expected_answer_points']
            assert a['answer'] == ''.join(e['data']['delta'] for e in a['events'] if e['event'] == 'answer_delta')
            for claim in r['claims']:
                assert claim['answer_quote'] in a['answer']
                for e in claim['evidence']:
                    source = next(s for s in a['sources'] if s['source_id'] == e['source_id'])
                    assert source['file_name'] == e['file_name']
                    assert source['text'][e['start_offset']-source['start_offset']:e['end_offset']-source['start_offset']] == e['quote']


def test_comparison_retains_both_sources_and_missing_reference_point():
    answer = next(a for a in read_jsonl(run.DIR/'answers.jsonl') if a['case_id'] == 'scope-compare-faqs')
    assert {s['file_name'] for s in answer['sources']} == {'masters-in-data-science-faq.txt', 'masters-in-data-science-faq-general.txt'}
    assert answer['coverage']['full_evidence_recall'] == 1
    assert answer['retrieval']['evidence_tokens'] <= 4096
    assert any('Admissions' in label for label in answer['sources'][0]['document_labels'])
    review = next(r for r in json.loads((run.DIR/'manual-review.json').read_text()) if r['case_id'] == answer['case_id'])
    assert review['named_source_compliance']
    assert not review['pass'] and not review['points'][1]['present']


def test_inventory_and_acceptance_preserve_failures():
    required = set(json.loads((BASELINE/'metrics.json').read_text())['metrics'])
    for directory in (run.DIR, RECOVERY):
        m = json.loads((directory/'metrics.json').read_text())['metrics']
        assert required - {'generated_service_seconds', 'generated_service_first_delta_seconds'} <= set(m)
        def check(entry):
            if 'status' not in entry:
                for child in entry.values():
                    check(child)
            elif entry['status'] == 'measured':
                assert entry['value'] is not None and entry['n'] > 0
                assert entry['method'] and entry['artifact']
            else:
                assert entry['status'] in ('not_applicable', 'unavailable')
                assert entry['value'] is None and entry['reason']
        for entry in m.values():
            check(entry)
        assert m['ingestion']['status'] == 'not_applicable'
        assert m['cost']['status'] == 'unavailable'
    first = json.loads((run.DIR/'acceptance.json').read_text())
    assert first['status'] == 'failed' and first['cases_passed'] == 9
    assert not first['gates']['latency'] and not first['gates']['all_requests_complete']
    assert not first['gates']['input_budget_complete_measurement']
    recovery = json.loads((RECOVERY/'acceptance.json').read_text())
    assert recovery['status'] == 'passed' and recovery['cases_total'] == 1
    assert len(read_jsonl(run.DIR/'calls.jsonl')) == 18
    assert len(read_jsonl(RECOVERY/'calls.jsonl')) == 2
