"""Full inventory for recorded service output and explicit Codex claim review."""
from copy import deepcopy
import json
from pathlib import Path
from statistics import mean

from evals import metrics
from evals.evaluate import digest,read_jsonl,timestamp,write_json
DIR=Path(__file__).parent


def summarize(cases,answers,reviews,calls,meta):
    rows=deepcopy(answers)
    for row in rows:
        # The collector's sum of zero embedding calls is not a timed stage.
        for key in ('embedding_seconds','scope_seconds','retrieval_seconds'):
            row[key]=row.get('retrieval',{}).get(key)
    result=metrics.summarize(cases,rows,[],meta,calls)
    m=result['metrics'];claims=[c for r in reviews for c in r['claims']];points=[p for r in reviews for p in r['points']]
    def score(key,values,method):
        m[key]=metrics.measured(mean(values),'fraction',len(values),method,'manual-review.json')
    score('answer_correctness',[p['correctness']/2 for p in points],'Micro-average v2 required points, 0/1/2; Codex, PLAN.md.')
    score('answer_completeness',[p['present'] for p in points],'Required points addressed; distinct from correctness.')
    score('faithfulness',[c['verdict']=='supported' for c in claims],'Every inventoried factual claim occurrence including extras/repeats; absence statements scored as abstention.')
    score('citation_support',[c['citation_verdict']=='supported' for c in claims for _ in c['associated_citations']],'Semantically associated claim/citation pairs; not ID validity.')
    score('citation_coverage',[bool(c['associated_citations']) and c['citation_verdict']=='supported' for c in claims],'Factual claims with local supporting citations; claim-free refusals exempt.')
    score('answer_relevance',[r['relevance']/2 for r in reviews],'0 off-topic, 1 extraneous, 2 responsive; independent from factual accuracy.')
    by={c['id']:c for c in cases};no=[r for r in reviews if not by[r['case_id']]['answerable']];yes=[r for r in reviews if by[r['case_id']]['answerable']]
    score('appropriate_abstention',[r['appropriate_abstention'] for r in no],'Unavailable answers and unresolved scope; four cases, two of each, shown separately.')
    score('incorrect_abstention',[r['incorrect_abstention'] for r in yes],'Answerable cases, including the FAQ comparison; denominator seven.')
    score('answerable_refusal',[r['abstains'] for r in yes],'Full/partial refusal on answerable questions.')
    score('functional_case_pass_rate',[r['pass'] for r in reviews],'PLAN.md required facts, claim/citation support, source scope and English.')
    score('english_compliance',[r['language_compliance'] for r in reviews],'Manual full-output inspection; names/code preserved.')
    score('named_source_compliance',[r['named_source_compliance'] for r in reviews],'Manual attribution against actual file identities.')
    score('personal_error_abstention',[r['appropriate_abstention'] for r in no if not r['case_id'].startswith('scope-')],'Two unavailable personal/API-error questions.')
    score('scope_clarification',[r['appropriate_abstention'] for r in no if r['case_id'].startswith('scope-')],'Two unresolved document requests; no provider call.')
    original=[p for r in reviews for p in r.get('original_rubric_points',[])]
    score('original_rubric_correctness',[p['correctness']/2 for p in original],'Original reference version for eight historical questions; optional awards details retained.')
    for key,value in [('claim_count',len(claims)),('unsupported_claims',sum(c['verdict']!='supported' for c in claims))]:
        m[key]=metrics.measured(value,'claims',len(reviews),'Full claim inventory; Codex.','manual-review.json')
    m['contradicted_claims']=metrics.missing('Support sufficiency recorded; no separate contradiction taxonomy.')
    for key in ('strict_pass_rate','judge_seconds','judge_reliability'):
        m[key]=metrics.missing('No paid judge; use recorded manual functional protocol.',False)
    m['token_usage']['judge']=metrics.missing('No judge calls.',False)
    m['model_loading']=metrics.missing('Local reranking disabled; no local inference model loaded.',False)
    m['scope_seconds']=metrics.timing([r.get('scope_seconds') for r in rows])
    m['scope_seconds']['method']+=' Identity lookup/resolution within retrieval; includes clarification paths.'
    m['embedding_seconds']['method']+=' Only executed query embedding stages; skipped calls excluded, not zero durations.'
    for key in ('total_seconds','first_delta_seconds'):
        m[key]['method']+=' In-process service, including queue/provider waits and persistence as applicable; excludes HTTP/browser. Includes two deterministic clarifications.'
    m['generated_service_seconds']=metrics.timing([r['total_seconds'] for r in rows if r.get('generation_seconds') is not None])
    m['generated_service_first_delta_seconds']=metrics.timing([r['first_delta_seconds'] for r in rows if r.get('generation_seconds') is not None])
    m['concurrency_throughput']=metrics.measured({'concurrency':1,'wall_seconds':meta['rag_wall_seconds'],'successful_requests_per_second':sum(r['status']=='ok' for r in rows)/meta['rag_wall_seconds']},'requests/second',len(rows),'Sequential service batch including logging; not load capacity.','run.json')
    result['reviewer']='Codex implementer, not independent human review'
    result['review_protocol']='PLAN.md'
    result['cases']=[{'case_id':r['case_id'],'pass':r['pass'],'points':r['points'],'findings':r['findings']} for r in reviews]
    return result


if __name__=='__main__':
    assert not (DIR/'acceptance.json').exists()
    cases=json.loads((DIR/'cases.json').read_text());answers=read_jsonl(DIR/'answers.jsonl');calls=read_jsonl(DIR/'calls.jsonl')
    reviews=json.loads((DIR/'manual-review.json').read_text());meta=json.loads((DIR/'run.json').read_text())
    report=summarize(cases,answers,reviews,calls,meta);m=report['metrics']
    write_json(DIR/'metrics.json',report)
    scope_checks=[]
    for a in answers:
        scope=a.get('retrieval',{}).get('document_scope')
        if scope:
            scope_checks.append({s['file_id'] for s in a['sources']}<=set(scope['file_ids']) and {c['file_id'] for c in a['retrieval']['candidates']}<=set(scope['file_ids']))
    gates={'all_requests_complete':len(answers)==len(cases) and all(a['status']=='ok' for a in answers),
           'all_manual_cases_pass':all(r['pass'] for r in reviews),'english':all(r['language_compliance'] for r in reviews),
           'scope_filter':all(scope_checks),'full_evidence_coverage':m['full_evidence_recall']['value']==1,
           'citation_ids':all(not a['citation_check']['invalid_source_ids'] for a in answers),
           'citation_coverage':m['citation_coverage']['value']>=.8 and all(any(c['associated_citations'] and c['citation_verdict']=='supported' for c in r['claims']) for r in reviews if r['claims']),
           'latency':m['total_seconds']['value']['mean']<=10 and m['total_seconds']['value']['p95']<=20 and m['first_delta_seconds']['value']['p95']<=10,
           'input_budget':max(c['usage']['input_tokens'] for c in calls if c['stage']=='generation')<=12000,
           'ingestion':meta['ingestion']['seconds']<=120}
    write_json(DIR/'acceptance.json',dict(evaluated_at=timestamp(),status='passed' if all(gates.values()) else 'failed',gates=gates,cases_passed=sum(r['pass'] for r in reviews),cases_total=len(reviews),paid_generation_calls=sum(c['stage']=='generation' for c in calls),paid_judge_calls=0))
    lines=['# Exact answers and Codex source review','','Protocol: [PLAN.md](PLAN.md). Original answers are unedited.','']
    by={a['case_id']:a for a in answers}
    for r in reviews:
        a=by[r['case_id']];assert digest(a['answer'].encode())==r['answer_sha256']
        lines+=['## '+r['case_id'],'',a['question'],'','### Unedited answer','',a['answer'],'','### Review','',f"Case: {'PASS' if r['pass'] else 'FAIL'}.",'']+['- '+f for f in r['findings']]+['']
        for c in r['claims']:
            assert c['answer_quote'] in a['answer']
            lines += [f"**{c['id']}** — {c['verdict']}; citations {c['associated_citations']}: {c['citation_verdict']}.",'','> '+c['answer_quote'],'',c['reason'],'']
            for e in c['evidence']:
                s=next(s for s in a['sources'] if s['source_id']==e['source_id'])
                assert s['text'][e['start_offset']-s['start_offset']:e['end_offset']-s['start_offset']]==e['quote']
                lines += [f"Source [{e['source_id']}] `{e['file_name']}` characters {e['start_offset']}:{e['end_offset']}:",'','```text',e['quote'],'```','']
    (DIR/'REVIEW.md').write_text('\n'.join(lines))
    print(json.dumps(gates,indent=2))
