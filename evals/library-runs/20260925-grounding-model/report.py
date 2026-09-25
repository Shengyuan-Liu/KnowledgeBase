"""Summarize the same five baseline/new answers using Codex's recorded assessments."""
import importlib
import json
from statistics import mean

from evals import metrics
from evals.evaluate import digest, read_jsonl, timestamp, write_json
run = importlib.import_module('evals.library-runs.20260925-grounding-model.run')
DIR, BASE = run.DIR, run.BASE


def summary(answers, reviews, calls, metadata):
    cases = json.loads((DIR/'cases.json').read_text())
    scored = metrics.summarize(cases, answers, [], {'top_k':5}, calls)
    m = scored['metrics']
    claims = [c for r in reviews for c in r['claims']]
    points = [p for r in reviews for p in r['points']]
    pairs = [c for c in claims for _ in c['associated_citations']]
    def value(key, values, method):
        m[key] = metrics.measured(mean(values), 'fraction', len(values), method, 'manual-review.json')
    value('answer_correctness', [p['correctness']/2 for p in points], 'Micro-average reference points, 0/1/2 correctness; frozen PLAN.md rubric; Codex.')
    value('answer_completeness', [int(p['present']) for p in points], 'Reference points addressed, independent of correctness.')
    value('faithfulness', [c['verdict']=='supported' for c in claims], 'Micro-average all inventoried factual claim occurrences, including repeats; missing information assessed as abstention.')
    value('citation_support', [c['citation_verdict']=='supported' for c in pairs], 'Micro-average semantically associated claim-citation pairs; exact source support, not ID validity.')
    value('citation_coverage', [bool(c['associated_citations']) and c['citation_verdict']=='supported' for c in claims], 'Claim occurrences with local supporting citations under frozen paragraph/list-item association rule.')
    value('answer_relevance', [r['relevance']/2 for r in reviews], '0 off-topic, 1 partial/extraneous, 2 responsive; Codex.')
    by = {c['id']:c for c in cases}
    unanswerable = [r for r in reviews if not by[r['case_id']]['answerable']]
    answerable = [r for r in reviews if by[r['case_id']]['answerable']]
    value('appropriate_abstention', [r['appropriate_abstention'] for r in unanswerable], 'Unavailable-information cases, denominator two.')
    value('incorrect_abstention', [r['incorrect_abstention'] for r in answerable], 'Answerable cases, denominator three.')
    value('answerable_refusal', [r['abstains'] for r in answerable], 'Any full/partial refusal on answerable cases.')
    value('functional_case_pass_rate', [r['pass'] for r in reviews], 'All required facts and associated citations supported; not v11 strict-pass scoring.')
    for key in ('claim_count','unsupported_claims'):
        m[key] = metrics.measured(len(claims) if key=='claim_count' else sum(c['verdict']!='supported' for c in claims),
            'claims',len(reviews),'Complete Codex factual-claim inventory; insufficient support is not proof of falsehood.','manual-review.json')
    m['contradicted_claims'] = metrics.missing('Manual protocol records support sufficiency; no separate contradiction taxonomy was scored.')
    for key in ('strict_pass_rate','judge_reliability','judge_seconds'):
        m[key] = metrics.missing('No v11 paid judge; manual functional protocol and per-case assessments retained.',False)
    for key in ('first_delta_seconds','total_seconds','retrieval_seconds','embedding_seconds','rerank_seconds','packing_seconds','search_fusion_seconds','ingestion','update_delete','model_loading'):
        m[key] = metrics.missing('Not exercised by fixed-context generation replay; baseline service measurements are retained separately.',False)
    for key in ('ingestion','query_embedding','judge'):
        m['token_usage'][key] = metrics.missing('No calls for this stage in the comparison.',False)
    for key in ('recall_at_k','precision_at_k','hit_rate_at_k','mrr_at_k','ndcg_at_k','annotated_char_recall','full_evidence_recall','evidence_tokens'):
        m[key]['origin'] = 'Inherited frozen baseline retrieval/context, unchanged; no fresh search/reranking measurement.'
        m[key]['artifact'] = str(BASE/'answers.jsonl')
    for key in ('generation_seconds','generation_first_delta_seconds'):
        m[key]['method'] += ' Provider generation stream only; includes provider waiting, excludes retrieval, persistence and HTTP transport.'
    m['reliability']['method'] = 'Planned saved-context generation requests/attempts; SDK retries zero, partial answers fail.'
    duration = metadata.get('generation_wall_seconds')
    m['concurrency_throughput'] = metrics.measured({'concurrency':1,'wall_seconds':duration,'successful_requests_per_second':sum(a['status']=='ok' for a in answers)/duration},
        'requests/second',len(answers),'Sequential generation batch including logging; no initialization, no load-capacity claim.','run.json') if duration else metrics.missing('No separately measured generation-only batch wall interval for the historical baseline.')
    scored.update(reviewer='Codex, same implementer; not independent human review',review_protocol='PLAN.md',
        limitations=['Five selected development/regression cases; not a new full service acceptance or held-out accuracy.',
                     'Same corpus, questions, user messages, configuration and annotations; only the answer model changes; messages and roles are unchanged. Tokenizers and provider defaults differ. Single historical sample, provider variability uncontrolled.',
                     'Historical scope judgments are conservative; compare actual output and supplied sources, not API behavior outside this corpus.',
                     'Actual billed cost unavailable. No local inference, live retrieval, service/browser timing or lifecycle exercise.'])
    scored['cases'] = [{'case_id':r['case_id'],'pass':r['pass'],'points':r['points'],'findings':r['findings']} for r in reviews]
    return scored


if __name__=='__main__':
    run.inputs()
    assert not (DIR/'acceptance.json').exists()
    meta=json.loads((DIR/'run.json').read_text())
    answers=read_jsonl(DIR/'answers.jsonl');calls=read_jsonl(DIR/'calls.jsonl')
    reviews=json.loads((DIR/'manual-review.json').read_text())
    old_answers=[a for a in read_jsonl(BASE/'answers.jsonl') if a['case_id'] in run.IDS]
    old_calls=[c for c in read_jsonl(BASE/'calls.jsonl') if c.get('case_id') in run.IDS and c['stage']=='generation']
    old_reviews=[r for r in json.loads((BASE/'manual-review.json').read_text()) if r['case_id'] in run.IDS]
    before=summary(old_answers,old_reviews,old_calls,json.loads((BASE/'run.json').read_text()))
    after=summary(answers,reviews,calls,meta)
    def qualify(entry):
        if isinstance(entry,dict):
            if entry.get('artifact') in ('answers.jsonl','manual-review.json','calls.jsonl','run.json'):
                entry['artifact']=str(BASE/entry['artifact'])
            for child in entry.values():qualify(child)
    qualify(before['metrics'])
    for entry in before['metrics'].values():
        if isinstance(entry,dict) and entry.get('artifact')==str(BASE/'manual-review.json'):entry['artifact']=str(BASE/'manual-review.json')
    write_json(DIR/'before-metrics.json',before);write_json(DIR/'after-metrics.json',after)
    m=after['metrics'];claims=[c for r in reviews for c in r['claims']]
    gates={'generation_success':len(answers)==5 and all(a['status']=='ok' for a in answers),
        'citation_ids':all(not a['citation_check']['invalid_source_ids'] for a in answers),
        'required_fact_correctness_and_scope':all(p['correctness']==2 for r in reviews for p in r['points']),
        'claim_support':all(c['verdict']=='supported' for c in claims),
        'associated_citation_support':all(c['citation_verdict']=='supported' for c in claims if c['associated_citations']),
        'citation_coverage':m['citation_coverage']['value']>=.8 and all(any(c['citation_verdict']=='supported' and c['associated_citations'] for c in r['claims']) for r in reviews if r['claims']),
        'abstention':m['appropriate_abstention']['value']==1 and m['incorrect_abstention']['value']==0,
        'generation_latency':m['generation_seconds']['value']['mean']<=10 and m['generation_seconds']['value']['p95']<=20 and m['generation_first_delta_seconds']['value']['p95']<=10,
        'input_budget':max(c['usage']['input_tokens'] for c in calls)<=12000}
    old_by={r['case_id']:r for r in old_reviews}
    comparison={'evaluated_at':timestamp(),'status':'passed' if all(gates.values()) else 'failed','gates':gates,
        'cases_passed':sum(r['pass'] for r in reviews),'cases_total':len(reviews),
        'per_case':[{'case_id':r['case_id'],'before_pass':old_by[r['case_id']]['pass'],'after_pass':r['pass'],'findings':r['findings']} for r in reviews],
        'resolved_models_before':sorted({c['resolved_model'] for c in old_calls}),
        'resolved_models_after':sorted({c['resolved_model'] for c in calls}),
        'reviewer':'Codex; not independent human review','paid_judge_calls':0,
        'decision':('Recommend the existing default functional v1 scope using the prior service/UI checks plus this targeted correction. No full-service rerun, broad quality guarantee or automatic merge.' if all(gates.values()) else 'Do not claim acceptance; retain failed gates and actual answers. No same-configuration retries or answer repair.')}
    write_json(DIR/'acceptance.json',comparison)
    lines=['# Recorded answers and Codex source review','','Frozen criteria: [PLAN.md](PLAN.md). Prior failed run remains unchanged.','']
    by={a['case_id']:a for a in answers}
    for r in reviews:
        a=by[r['case_id']]
        assert digest(a['answer'].encode())==r['answer_sha256']
        lines += ['## '+r['case_id'],'',a['question'],'','### Unedited answer','',a['answer'],'','### Review','',f"Case: {'PASS' if r['pass'] else 'FAIL'}.",'']
        lines += ['- '+s for s in r['findings']]+['']
        for c in r['claims']:
            assert c['answer_quote'] in a['answer']
            lines += [f"**{c['id']}** — {c['verdict']}; associated citations {c['associated_citations']}: {c['citation_verdict']}.",'', '> '+c['answer_quote'],'',c['reason'],'']
            for e in c['evidence']:
                s=next(s for s in a['sources'] if s['source_id']==e['source_id'])
                assert s['text'][e['start_offset']-s['start_offset']:e['end_offset']-s['start_offset']]==e['quote']
                lines += [f"Source [{e['source_id']}] `{e['file_name']}` characters {e['start_offset']}:{e['end_offset']}:",'','```text',e['quote'],'```','']
    (DIR/'REVIEW.md').write_text('\n'.join(lines))
    print(json.dumps(comparison,indent=2))
    for key in ('answer_correctness','faithfulness','citation_support','citation_coverage','generation_seconds','generation_first_delta_seconds','token_usage'):
        print(key,m[key])
