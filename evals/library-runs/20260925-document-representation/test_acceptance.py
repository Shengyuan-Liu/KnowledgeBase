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


def test_completed_run_preserves_streams_and_stops_unresolved_scopes():
    if not (run.DIR/'answers.jsonl').exists():
        pytest.skip('Preflight: no live results yet.')
    rows=read_jsonl(run.DIR/'answers.jsonl');calls=read_jsonl(run.DIR/'calls.jsonl')
    assert len(rows)==11
    for a in rows:
        assert a['status']=='ok'
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
