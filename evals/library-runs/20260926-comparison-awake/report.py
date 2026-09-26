"""Retain the single awake-host acceptance and its limitations."""
import importlib
import json
from pathlib import Path
from evals import metrics
from evals.evaluate import digest, read_jsonl, timestamp, write_json

DIR=Path(__file__).parent
BASE=DIR.parent/'20260925-document-representation'
protocol=importlib.import_module('evals.library-runs.20260925-document-scope.report')

if __name__=='__main__':
    assert not (DIR/'metrics.json').exists()
    cases=json.loads((DIR/'cases.json').read_text());answers=read_jsonl(DIR/'answers.jsonl');calls=read_jsonl(DIR/'calls.jsonl')
    reviews=json.loads((DIR/'manual-review.json').read_text());meta=json.loads((DIR/'run.json').read_text())
    result=protocol.summarize(cases,answers,reviews,calls,meta);m=result['metrics']
    for key in ('total_wall_seconds','first_delta_wall_seconds','generation_wall_seconds','generation_first_delta_wall_seconds'):
        m[key]=metrics.timing([r.get(key) for r in answers if r['status']=='ok'])
        m[key]['method']+=' Wall elapsed, including any suspension/clock change; no transitions recorded during this batch.'
    m['stream_open_seconds']=metrics.timing([c['stream_open_seconds'] for c in calls if c['stage']=='generation'])
    m['stream_open_wall_seconds']=metrics.timing([c['stream_open_wall_seconds'] for c in calls if c['stage']=='generation'])
    for key in ('stream_open_seconds','stream_open_wall_seconds'):
        m[key]['artifact']='calls.jsonl'
        m[key]['method']+=' SDK create to receiving the streaming response; not first answer delta.'
    m['max_service_clock_difference']=metrics.measured(max(abs(a['total_seconds']-a['total_wall_seconds']) for a in answers),'seconds',len(answers),'Maximum absolute active/wall elapsed divergence; not adjusted away.')
    m['token_usage']['ingestion']=metrics.missing('Verified existing index copied; no ingestion calls.',False)
    m['ingestion']=metrics.missing('No fresh ingestion; unchanged source/index snapshots verified against the baseline.',False)
    m['update_delete']=metrics.missing('Not exercised by this live query batch; see offline workflow checks.',False)
    m['rerank_seconds']=metrics.missing('Local reranking disabled.',False)
    m['fully_correct_points']=metrics.measured(sum(p['correctness']==2 for r in reviews for p in r['points'])/sum(len(r['points']) for r in reviews),'fraction',sum(len(r['points']) for r in reviews),'Frozen v2 expected points, explicit Codex review.','manual-review.json')
    m['runtime_warnings']=metrics.measured({'unraisable_async_generator_warnings':(DIR/'run.log').read_text().count('Exception ignored in:')},'warnings',1,'Raw stderr inspection; request success does not erase runtime warnings.','run.log')
    result['limitations'] += ['A non-fatal BoundAsyncStream async-generator finalizer warning remains in run.log; not reproduced in 25 offline SDK streams with forced collection. All requests completed and persisted, but absence of a resource leak is not established for every provider transport.',
        'Some responses repeat their conclusion; comparison absence is phrased page-wide but matches this inspected frozen document. These style/wording limits are not a changed factual rubric.',
        'Host was kept awake for this batch; previous performance is sleep-confounded, so the comparison is descriptive, not isolated provider improvement.']
    write_json(DIR/'metrics.json',result)
    (DIR/'METRICS.md').write_text('# Complete metric inventory\n\n'+'\n'.join(metrics.console_lines(result))+'\n')
    def latency(total,first):
        return m[total]['value']['mean']<=10 and m[total]['value']['p95']<=20 and m[first]['value']['p95']<=10
    scope=[]
    for a in answers:
        d=a.get('retrieval',{}).get('document_scope')
        if d:
            scope.append({s['file_id'] for s in a['sources']}<=set(d['file_ids']) and {c['file_id'] for c in a['retrieval']['candidates']}<=set(d['file_ids']))
    generation=[c for c in calls if c['stage']=='generation']
    gates=dict(all_requests_complete=len(answers)==11 and all(a['status']=='ok' for a in answers),
        all_manual_cases_pass=all(r['pass'] for r in reviews),english=all(r['language_compliance'] for r in reviews),
        scope_filter=all(scope),full_evidence_coverage=m['full_evidence_recall']['value']==1,
        citations=all(not a['citation_check']['invalid_source_ids'] for a in answers) and m['citation_support']['value']==1 and m['citation_coverage']['value']>=.8,
        latency_active=latency('total_seconds','first_delta_seconds'),latency_wall=latency('total_wall_seconds','first_delta_wall_seconds'),
        input_budget=all(c.get('usage') and c['usage']['input_tokens']<=12000 for c in generation),
        index_copy=(DIR/'chunks.json').read_bytes()==(BASE/'chunks.json').read_bytes())
    write_json(DIR/'acceptance.json',dict(evaluated_at=timestamp(),status='passed' if all(gates.values()) else 'failed',gates=gates,
        cases_passed=sum(r['pass'] for r in reviews),cases_total=len(reviews),paid_calls=len(calls),paid_generation_calls=len(generation),paid_judge_calls=0,
        warning='One non-fatal async-generator finalizer warning retained; no zero-warning claim.',merge_authorized=False))
    old={a['case_id']:a for a in read_jsonl(BASE/'answers.jsonl')}
    old_reviews={r['case_id']:r for r in json.loads((BASE/'manual-review.json').read_text())}
    comparison=[]
    for a,r in zip(answers,reviews,strict=True):
        assert a['case_id']==r['case_id']
        b=old[a['case_id']]
        comparison.append(dict(case_id=a['case_id'],before_status=b['status'],after_status=a['status'],
            before_pass=old_reviews[a['case_id']]['pass'],after_pass=r['pass'],before_points=old_reviews[a['case_id']]['points'],after_points=r['points'],
            before_coverage=b.get('coverage'),after_coverage=a.get('coverage'),before_service_seconds=b['total_seconds'],after_service_seconds=a['total_seconds'],after_wall_seconds=a['total_wall_seconds'],findings=r['findings']))
    write_json(DIR/'comparison.json',dict(before_run=str(BASE),after_run=str(DIR),cases=comparison,
        caveats=['Original first pass retained, not replaced by recovery.', 'Same frozen cases/corpus/annotations and index; prompt and awake-host conditions change.', 'No causal timing attribution or held-out accuracy claim.']))
    print(json.dumps(gates,indent=2))
    for key in ('total_seconds','first_delta_seconds','generation_seconds','generation_first_delta_seconds','full_evidence_recall','claim_count','max_service_clock_difference','token_usage'):
        print(key,json.dumps(m[key]))
