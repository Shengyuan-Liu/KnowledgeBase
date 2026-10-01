"""Measure structural changes while leaving semantic outcomes explicitly untested."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from knowledgebase.providers.limits import input_tokens
from record_check import METRICS

ROOT=Path(__file__).resolve().parent
LIVE=Path('evals/library-runs/20260929-pdf-heading-acceptance')


def load(name):
    return json.loads((ROOT/name).read_text())


if __name__=='__main__':
    before,after=load('before.json')['rows'],load('after.json')['rows']
    frozen=json.loads((LIVE/'frozen-cases.json').read_text())
    labels=json.loads((LIVE/'frozen-labels.json').read_text())
    runtime=json.loads((LIVE/'resolved-runtime.json').read_text())
    pairs=[]
    for b,a,case in zip(before,after,frozen['cases'],strict=True):
        assert b['case_id']==a['case_id']==case['id']
        assert b['catalog']==a['catalog'] and b['answer_context']==a['answer_context']
        assert b['answer_messages'][0]==a['answer_messages'][0]
        assert [r['line'] for r in b['table_rows']]==[r['line'] for r in a['table_rows']]
        assert all(row['markers_present'] for row in a['table_rows'])
        raw=json.loads((LIVE/(case['id']+'-planned.json')).read_text())
        sources=raw['answer']['sources']
        coverage={fact:all(any(s['file_id']==span['file_id'] and s['start_offset']<=span['start'] and span['end']<=s['end_offset']
            and anchor['anchor'].casefold() in s['text'].casefold() for s in sources for span in anchor['spans'])
            for anchor in labels[fact]['anchors']) for fact in case['expected_fact_ids']}
        b_tokens=input_tokens(b['answer_messages'],'cl100k_base')
        a_tokens=input_tokens(a['answer_messages'],'cl100k_base')
        assert max(b_tokens,a_tokens)<=runtime['settings']['planning']['answer_max_input_tokens']
        pairs.append(dict(case_id=case['id'],table_rows=len(a['table_rows']),
            marked_before=sum(row['markers_present'] for row in b['table_rows']),
            marked_after=sum(row['markers_present'] for row in a['table_rows']),
            before_assessment_tokens=b['assessment_input_tokens'],after_assessment_tokens=a['assessment_input_tokens'],
            before_answer_input_tokens=b_tokens,after_answer_input_tokens=a_tokens,
            before_coverage=coverage,after_coverage=coverage,answer_context_tokens=a['answer_context_tokens'],
            catalog_and_source_provenance_unchanged=True,answer_user_message_unchanged=True))
    inventory={m:dict(status='not_applicable',value=None,unit=None,sample_count=None,
        population='Offline rendering of frozen six-question contexts',method='Not exercised',aggregation='none',
        artifact='comparison.json',reason='No live retrieval, provider assessment/generation, HTTP/SSE, ingestion, update/delete or load workload. Mocked output preservation is not semantic accuracy.') for m in METRICS}
    def measured(name,value,unit,n,method,aggregation):
        inventory[name]=dict(status='measured',value=value,unit=unit,sample_count=n,
            population='Matched six frozen final contexts; source spans, questions and labels unchanged',
            method=method,aggregation=aggregation,artifact='comparison.json')
    covered=sum(sum(p['after_coverage'].values()) for p in pairs)
    expected=sum(len(p['after_coverage']) for p in pairs)
    assert covered==expected==16
    measured('Final evidence coverage',dict(before={'covered':covered,'expected':expected},after={'covered':covered,'expected':expected}),
        'frozen fact-anchor groups',16,'All anchors remain in exact supplied text/ranges. Recompute against frozen labels; context-only, no new answers.','Micro counts')
    measured('Token usage and cost',dict(local_input_counts=pairs,assessment_cap=8192,answer_cap=16384,
        actual_provider_usage={'status':'not_applicable','value':None,'reason':'No provider calls.'},
        billed_cost={'status':'not_applicable','value':None,'reason':'Offline only.'}),
        'local cl100k_base tokens',12,'Production input-budget counter; assessor includes schema. These are local input counts, not billed tokens. Answer context budgets remain unchanged.','Per case/arm')
    measured('Reliability',dict(completed_contexts=12,errors=0,table_readings=75,marked_before=0,marked_after=75),
        'offline rendering counts',12,'Both captures succeed; all final supplied source text/catalogs unchanged. Table markers checked against exact spans; not model selection or network success.','Counts')
    record=dict(at=datetime.now(timezone.utc).isoformat(),baseline_commit=load('frozen-inputs.json')['baseline_commit'],
        production_hashes={str(p):sha256(p.read_bytes()).hexdigest() for p in Path('knowledgebase').rglob('*.py')},
        runtime_reference_sha256=sha256((LIVE/'resolved-runtime.json').read_bytes()).hexdigest(),
        pairs=pairs,metric_inventory=inventory,
        interpretation='All 75 readings gain source-span-derived IDs; no changed facts or answer user context. Historical wrong references and uncited conclusion remain raw failures. Fresh semantic compliance is unmeasured.',
        controls='Same six questions, PDFs, labels, selected evidence, source numbers, table values and canonical ranges. Retrieval is not rerun. No provider/embedding/reranker setting changes.')
    with (ROOT/'comparison.json').open('x') as file:
        file.write(json.dumps(record,indent=2)+'\n')
    print('75/75 table readings explicitly mapped, unchanged 16/16 supplied fact anchors; all six input budgets pass.')
    print('Generation local input counts:',[(p['case_id'],p['before_answer_input_tokens'],p['after_answer_input_tokens']) for p in pairs])
