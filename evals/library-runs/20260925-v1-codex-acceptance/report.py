"""Apply frozen gates to preserved service observations and Codex claim assessments."""
from copy import deepcopy
import json
from pathlib import Path
from statistics import mean
from evals import metrics
from evals.evaluate import digest,git_state,read_jsonl,retrieval_metrics,timestamp,write_json
DIR=Path(__file__).parent

if __name__=='__main__':
    assert not (DIR/'acceptance.json').exists()
    run=json.loads((DIR/'run.json').read_text());frozen=json.loads((DIR/'freeze.json').read_text())
    assert digest((DIR/'PLAN.md').read_bytes())==run['plan_sha256']
    assert digest((DIR/'cases.json').read_bytes())==frozen['cases_sha256']
    cases=json.loads((DIR/'cases.json').read_text());case_by={c['id']:c for c in cases}
    answers=read_jsonl(DIR/'answers.jsonl');answer_by={a['case_id']:a for a in answers}
    reviews=json.loads((DIR/'manual-review.json').read_text());calls=read_jsonl(DIR/'calls.jsonl')
    chunks=json.loads((DIR/'chunks.json').read_text());chunk_by={c['chunk_id']:c for c in chunks}
    automatic=json.loads((DIR/'automatic-metrics.json').read_text());scored=deepcopy(automatic)
    metric=scored['metrics'];claims=[c for r in reviews for c in r['claims']];points=[p for r in reviews for p in r['points']]
    for r in reviews:
        assert r['answer_sha256']==digest(answer_by[r['case_id']]['answer'].encode())
        for c in r['claims']:
            assert c['answer_quote'] in answer_by[r['case_id']]['answer']
            for e in c['evidence']:
                source=next(s for s in answer_by[r['case_id']]['sources'] if s['source_id']==e['source_id'])
                assert source['text'][e['start_offset']-source['start_offset']:e['end_offset']-source['start_offset']]==e['quote']
    artifact='manual-review.json'
    metric['answer_correctness']=metrics.measured(mean(p['correctness']/2 for p in points),'fraction',len(points),'Micro-average 0/1/2 reference-point correctness, Codex review; partial credit for correct base field status with unsupported universal scope.',artifact)
    metric['answer_completeness']=metrics.measured(mean(int(p['present']) for p in points),'fraction',len(points),'Required points addressed; separate from correctness.',artifact)
    metric['faithfulness']=metrics.measured(mean(c['verdict']=='supported' for c in claims),'fraction',len(claims),'Micro-average inventoried factual claim occurrences; missing-information statements assessed separately; all output paragraphs inspected by Codex.',artifact)
    metric['answer_relevance']=metrics.measured(mean(r['relevance']/2 for r in reviews),'fraction',len(reviews),'Codex 0 off-topic / 1 partly responsive / 2 responsive; correctness assessed separately.',artifact)
    pairs=[c for c in claims for identity in c['associated_citations']]
    metric['citation_support']=metrics.measured(mean(c['citation_verdict']=='supported' for c in pairs),'fraction',len(pairs),'Semantically associated claim-citation pairs; unrelated references within a shared paragraph are not assigned to every clause. All associations are recorded.',artifact)
    metric['citation_coverage']=metrics.measured(mean(bool(c['associated_citations']) and c['citation_verdict']=='supported' for c in claims),'fraction',len(claims),'Claim occurrences with a local supporting citation under the preregistered paragraph/list-item rule. Not directly comparable to v11.',artifact)
    answerable=[r for r in reviews if case_by[r['case_id']]['answerable']];missing=[r for r in reviews if not case_by[r['case_id']]['answerable']]
    metric['appropriate_abstention']=metrics.measured(mean(r['appropriate_abstention'] for r in missing),'fraction',len(missing),'Both unavailable-information cases; no invented error or personal assignment.',artifact)
    metric['incorrect_abstention']=metrics.measured(mean(r['incorrect_abstention'] for r in answerable),'fraction',len(answerable),'Answerable-case refusal despite sufficient evidence.',artifact)
    metric['answerable_refusal']=metrics.measured(mean(r['abstains'] for r in answerable),'fraction',len(answerable),'Any full/partial refusal on answerable cases.',artifact)
    metric['judge_reliability']=metrics.missing('No paid judge was run. Codex reviewed all eight outputs against the frozen manual protocol.',False)
    metric['judge_seconds']=metrics.missing('No judge API request; reviewer reading time not separately instrumented.',False)
    metric['token_usage']['judge']=metrics.missing('No judge provider calls.',False)
    metric['model_loading']=metrics.missing('Local reranking disabled; no local inference model loaded.',False)
    for key in ('first_delta_seconds','total_seconds'):
        metric[key]['method']+=' In-process streamed RAG service, including persistence at completion, excluding HTTP/browser transport.'
    stages=[]
    for case in cases:
        row=answer_by[case['id']];trace=row['retrieval'];entry={'case_id':case['id'],'stages':{}}
        for name,ranked in [('vector_candidates',trace['vector_matches']),('bm25_candidates',trace['bm25_matches']),('fused_candidates',trace['fused_matches']),('selected_children',trace['candidates'])]:
            hits=[chunk_by[r['chunk_id']] for r in ranked]
            entry['stages'][name]={'input_count':len(ranked),'ranking':metrics.ranking(case,ranked,chunks,5),'source_span_coverage':retrieval_metrics(case,hits)}
        entry['stages']['supplied_evidence']={'source_span_coverage':retrieval_metrics(case,row['sources'])}
        stages.append(entry)
    write_json(DIR/'stage-metrics.json',stages)
    scored.update(reviewer='Codex, same agent as implementer/test author; not independent human review.',review_protocol='PLAN.md frozen before outputs',
        limitations=['Eight new questions on a familiar corpus, not independent held-out accuracy.', 'Manual semantic assessments include judgment calls; raw answers/evidence and reasons are retained.', 'No production change in this acceptance run; green engineering checks reused.', 'Single sequential service run, no HTTP/UI latency or concurrency study; actual billing unavailable.'])
    write_json(DIR/'reviewed-metrics.json',scored)
    gen=[c for c in calls if c['stage']=='generation'];max_input=max(c['usage']['input_tokens'] for c in gen)
    gates={
        'service_success':len(answers)==8 and all(a['status']=='ok' for a in answers) and all(c['status']=='ok' for c in calls),
        'evidence_budget_and_citation_ids':all(a['retrieval']['evidence_tokens']<=4096 and not a['citation_check']['invalid_source_ids'] for a in answers),
        'reference_evidence_coverage':all(a['coverage']['annotated_char_recall']==1 for a in answers if case_by[a['case_id']]['answerable']),
        'required_fact_correctness_and_scope':all(p['correctness']==2 for p in points),
        'abstention':all(r['appropriate_abstention'] for r in missing) and not any(r['incorrect_abstention'] for r in answerable),
        'associated_citation_support':all(c['citation_verdict']=='supported' for c in pairs),
        'citation_coverage':metric['citation_coverage']['value']>=.8 and all(any(c['associated_citations'] and c['citation_verdict']=='supported' for c in r['claims']) for r in reviews if r['claims']),
        'latency':metric['total_seconds']['value']['mean']<=10 and metric['total_seconds']['value']['p95']<=20 and metric['first_delta_seconds']['value']['p95']<=10,
        'input_budget':max_input<=12000,'ingestion':run['ingestion']['seconds']<=120}
    verdict={'evaluated_at':timestamp(),'git':git_state(),'status':'passed' if all(gates.values()) else 'failed',
        'gates':gates,'cases_passed':sum(r['pass'] for r in reviews),'cases_total':len(reviews),'maximum_generation_input_tokens':max_input,
        'reviewer':'Codex','review_not_independent':True,'changes_to_criteria_or_answers':False,'paid_judge_calls':0,
        'blockers':[{'case_id':r['case_id'],'claim':c['statement'],'answer_quote':c['answer_quote'],'reason':c['reason']} for r in reviews for c in r['claims'] if c['verdict']!='supported'],
        'decision':'Do not claim unconditional acceptance under the frozen scope/support criteria. Engineering and operational checks pass, but one answer broadens a table entry into an unsupported all-endpoint guarantee. No automatic merge, output repair or re-run.'}
    write_json(DIR/'acceptance.json',verdict)
    print('Acceptance:',verdict['status'],'cases',verdict['cases_passed'],'/',len(reviews))
    for key in ('answer_correctness','faithfulness','citation_support','citation_coverage','first_delta_seconds','total_seconds'):print(key,metric[key]['value'])
