"""Validate frozen source scope before calls and raw acceptance artifacts later."""
import importlib
import json
from pathlib import Path

import pytest
from evals.evaluate import read_jsonl
from knowledgebase.rag.scope import document_references,identity_labels,resolve_document_scope
from knowledgebase.schemas import ScopeFile
run=importlib.import_module('evals.library-runs.20260926-comparison-awake.run')


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



def test_complete_batch_preserves_raw_events_scope_and_provider_usage():
    from evals.evaluate import digest
    rows=read_jsonl(run.DIR/'answers.jsonl');calls=read_jsonl(run.DIR/'calls.jsonl')
    assert len(rows)==11 and all(a['status']=='ok' for a in rows)
    assert len(calls)==18 and all(c['status']=='ok' and c['usage'] for c in calls)
    assert sum(c['stage']=='generation' for c in calls)==9
    frozen=json.loads((run.DIR/'freeze.json').read_text())
    for a in rows:
        assert a['answer']==''.join(e['data']['delta'] for e in a['events'] if e['event']=='answer_delta')
        assert a['events'][-1]['event']=='complete'
        assert a['total_wall_seconds']>=a['first_delta_wall_seconds']>=0
        assert abs(a['total_seconds']-a['total_wall_seconds'])<.01
        scope=a['retrieval']['document_scope']
        if scope:
            assert {s['file_id'] for s in a['sources']}<=set(scope['file_ids'])
            assert {c['file_id'] for c in a['retrieval']['candidates']}<=set(scope['file_ids'])
            if scope['status']!='resolved':
                assert not a['sources'] and not [c for c in calls if c['case_id']==a['case_id']]
        assert a['retrieval']['evidence_tokens']<=4096
    for c in calls:
        if c['stage']=='generation':
            assert digest(c['messages'][1]['content'].encode())==frozen['prompt_sha256']
            assert c['resolved_model']=='gpt-4.1-2025-04-14' and c['reasoning'] is None
            assert c['wall_seconds']>=c['stream_open_wall_seconds']>=0
            assert c['finished_at']


def test_reviews_have_exact_quotes_offsets_and_frozen_points():
    from evals.evaluate import digest
    rows={a['case_id']:a for a in read_jsonl(run.DIR/'answers.jsonl')}
    cases={c['id']:c for c in json.loads((run.DIR/'cases.json').read_text())}
    reviews=json.loads((run.DIR/'manual-review.json').read_text())
    assert len(reviews)==11
    for r in reviews:
        a=rows[r['case_id']]
        assert r['answer_sha256']==digest(a['answer'].encode())
        assert [p['reference'] for p in r['points']]==cases[r['case_id']]['expected_answer_points']
        for c in r['claims']:
            assert c['answer_quote'] in a['answer']
            for e in c['evidence']:
                s=next(s for s in a['sources'] if s['source_id']==e['source_id'])
                assert e['file_name']==s['file_name']
                assert s['text'][e['start_offset']-s['start_offset']:e['end_offset']-s['start_offset']]==e['quote']
    compared=rows['scope-compare-faqs']
    assert {s['file_name'] for s in compared['sources']}=={'masters-in-data-science-faq.txt','masters-in-data-science-faq-general.txt'}
    assert compared['coverage']['full_evidence_recall']==1


def test_completed_answers_and_evidence_are_persisted_in_isolated_index():
    import sqlite3
    meta=json.loads((run.DIR/'run.json').read_text())
    database=Path(meta['config']['data_dir'])/'evals'/run.DIR.name/'knowledgebase.db'
    if not database.exists():
        pytest.skip('Local isolated acceptance index not retained on this checkout.')
    with sqlite3.connect(f'file:{database.resolve()}?mode=ro',uri=True) as conn:
        for a in read_jsonl(run.DIR/'answers.jsonl'):
            messages=conn.execute('SELECT message_id,role,content FROM messages WHERE conversation_id=? ORDER BY message_id',(a['conversation_id'],)).fetchall()
            assert [(m[1],m[2]) for m in messages]==[('user',a['question']),('assistant',a['answer'])]
            message_id=messages[-1][0]
            sources,citations=conn.execute('SELECT sources,citation_check FROM answer_snapshots WHERE message_id=?',(message_id,)).fetchone()
            diagnostics,=conn.execute('SELECT diagnostics FROM retrieval_snapshots WHERE message_id=?',(message_id,)).fetchone()
            assert json.loads(sources)==a['sources'] and json.loads(citations)==a['citation_check']
            assert json.loads(diagnostics)==a['retrieval']


def test_report_preserves_inventory_warning_and_historical_failure():
    m=json.loads((run.DIR/'metrics.json').read_text())['metrics']
    prior=run.DIR.parent/'20260925-document-representation'
    assert set(json.loads((prior/'automatic-metrics.json').read_text())['metrics'])<=set(m)
    def validate(entry):
        if 'status' not in entry:
            for child in entry.values():validate(child)
        elif entry['status']=='measured':
            assert entry['value'] is not None and entry['n']>0 and entry['artifact'] and entry['method']
        else:
            assert entry['status'] in ('unavailable','not_applicable') and entry['value'] is None and entry['reason']
    for entry in m.values():validate(entry)
    assert m['runtime_warnings']['value']['unraisable_async_generator_warnings']==1
    assert 'Exception ignored in:' in (run.DIR/'run.log').read_text()
    assert json.loads((prior/'acceptance.json').read_text())['status']=='failed'
    acceptance=json.loads((run.DIR/'acceptance.json').read_text())
    assert acceptance['status']=='passed' and not acceptance['merge_authorized']
    assert (run.DIR/'power-events-during.log').read_text().strip()==''
    for name in ['power-assertions-before.log','power-assertions-after.log']:
        assert 'caffeinate' in (run.DIR/name).read_text()
