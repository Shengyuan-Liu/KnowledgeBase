"""Retain two annotation versions without rewriting any historical result."""
from copy import deepcopy
import importlib
import json
from statistics import mean

from evals import metrics
from evals.evaluate import digest, read_jsonl, timestamp, write_json
run = importlib.import_module('evals.library-runs.20260925-answer-focus.run')
legacy = importlib.import_module('evals.library-runs.20260925-grounding-high.report')
DIR, BASE = run.DIR, run.BASE
# Reuse the retained metric inventory and timing aggregation, with explicit scope.
legacy.DIR, legacy.BASE = DIR, BASE


def summary(answers, reviews, calls, metadata, artifact):
    result=legacy.summary(answers,reviews,calls,metadata)
    result['limitations']=[
        'Five known development cases, not held-out accuracy or full-service acceptance.',
        'Historical single GPT-4.1 sample versus one new sample; only prompt changes, provider variability uncontrolled.',
        'Question-aligned annotations v2 change two awards points after historical output inspection, frozen before new output. Old scores retained separately.',
        'Same Codex implementer/reviewer; no paid judge or independent human review.',
        'Generation only; no fresh retrieval, ingestion, lifecycle or HTTP measurement. Billed cost unavailable.'
    ]
    m=result['metrics']
    m['functional_case_pass_rate']['method']='All question-aligned points, supported claims/citations, named-source scope, abstention and English compliance; PLAN.md.'
    for key,field in [('english_compliance','language_compliance'),('named_source_compliance','named_source_compliance')]:
        m[key]=metrics.measured(mean(r[field] for r in reviews),'fraction',len(reviews),'Manual full-output review; PLAN.md.',artifact)
    m['original_rubric_correctness']=metrics.measured(mean(p['correctness']/2 for r in reviews for p in r['original_rubric_points']),
        'fraction',sum(len(r['original_rubric_points']) for r in reviews),'Original reference points including optional details; retained for transparent comparison.',artifact)
    result['review_artifact']=artifact
    return result


if __name__=='__main__':
    run.inputs()
    assert not (DIR/'acceptance.json').exists()
    answers=read_jsonl(DIR/'answers.jsonl'); calls=read_jsonl(DIR/'calls.jsonl')
    reviews=json.loads((DIR/'manual-review.json').read_text())
    old_reviews=deepcopy(json.loads((BASE/'manual-review.json').read_text()))
    by={c['id']:c for c in json.loads((DIR/'cases.json').read_text())}
    for r in old_reviews:
        r['original_rubric_points']=deepcopy(r['points'])
        r['language_compliance']=True
        r['named_source_compliance']=r['case_id']!='accept-awards-jobs'
        if r['case_id']=='accept-awards-jobs':
            for p,new in zip(r['points'],by[r['case_id']]['expected_answer_points'],strict=True):
                p.update(reference=new,correctness=2)
            r['findings'].append('V2 removes unrequested award-count requirement; existing wrong-source attribution still fails. Original review is unchanged.')
        # None of the failed baseline cases becomes passing under the correction.
    write_json(DIR/'baseline-v2-review.json',old_reviews)
    before=summary(read_jsonl(BASE/'answers.jsonl'),old_reviews,read_jsonl(BASE/'calls.jsonl'),json.loads((BASE/'run.json').read_text()),'baseline-v2-review.json')
    after=summary(answers,reviews,calls,json.loads((DIR/'run.json').read_text()),'manual-review.json')
    def qualify(entry):
        if isinstance(entry,dict):
            if entry.get('artifact') in ('answers.jsonl','calls.jsonl','run.json'):
                entry['artifact']=str(BASE/entry['artifact'])
            elif entry.get('artifact')=='manual-review.json':entry['artifact']='baseline-v2-review.json'
            for child in entry.values():qualify(child)
    qualify(before['metrics'])
    write_json(DIR/'before-metrics.json',before);write_json(DIR/'after-metrics.json',after)
    m=after['metrics'];claims=[c for r in reviews for c in r['claims']]
    gates={
        'generation_success':len(answers)==5 and all(a['status']=='ok' for a in answers),
        'citation_ids':all(not a['citation_check']['invalid_source_ids'] for a in answers),
        'question_aligned_required_facts':all(p['correctness']==2 for r in reviews for p in r['points']),
        'claim_support':all(c['verdict']=='supported' for c in claims),
        'associated_citation_support':all(c['citation_verdict']=='supported' for c in claims if c['associated_citations']),
        'named_source_scope':all(r['named_source_compliance'] for r in reviews),
        'english':all(r['language_compliance'] for r in reviews),
        'citation_coverage':m['citation_coverage']['value']>=.8 and all(any(c['associated_citations'] and c['citation_verdict']=='supported' for c in r['claims']) for r in reviews if r['claims']),
        'abstention':m['appropriate_abstention']['value']==1 and m['incorrect_abstention']['value']==0,
        'generation_latency':m['generation_seconds']['value']['mean']<=10 and m['generation_seconds']['value']['p95']<=20 and m['generation_first_delta_seconds']['value']['p95']<=10,
        'input_budget':max(c['usage']['input_tokens'] for c in calls)<=12000}
    comparison={'evaluated_at':timestamp(),'status':'passed' if all(gates.values()) else 'failed','gates':gates,
        'cases_passed':sum(r['pass'] for r in reviews),'cases_total':len(reviews),
        'before_cases_passed':sum(r['pass'] for r in old_reviews),
        'per_case':[{'case_id':r['case_id'],'before_pass':next(o['pass'] for o in old_reviews if o['case_id']==r['case_id']), 'after_pass':r['pass'],'findings':r['findings']} for r in reviews],
        'resolved_models':sorted({c['resolved_model'] for c in calls}), 'paid_generation_calls':len(calls),'paid_judge_calls':0,
        'decision':'Source-specific answer scope still fails. No further sampling, model/config change, output repair or merge. Do not claim full acceptance.'}
    write_json(DIR/'acceptance.json',comparison)
    lines=['# Exact answers and source review','','Protocol: [PLAN.md](PLAN.md). Both reference versions retained. Reviewer: Codex, not independent human.','']
    by_answer={a['case_id']:a for a in answers}
    for r in reviews:
        a=by_answer[r['case_id']]
        assert digest(a['answer'].encode())==r['answer_sha256']
        lines += ['## '+r['case_id'],'',a['question'],'','### Unedited answer','',a['answer'],'','### Review','',f"Case: {'PASS' if r['pass'] else 'FAIL'}.",'']
        lines += ['- '+f for f in r['findings']]+['']
        for c in r['claims']:
            assert c['answer_quote'] in a['answer']
            lines += [f"**{c['id']}**: {c['verdict']}; associated citations {c['associated_citations']}: {c['citation_verdict']}.",'','> '+c['answer_quote'],'',c['reason'],'']
            for e in c['evidence']:
                s=next(s for s in a['sources'] if s['source_id']==e['source_id'])
                assert s['text'][e['start_offset']-s['start_offset']:e['end_offset']-s['start_offset']]==e['quote']
                lines += [f"Source [{e['source_id']}] `{e['file_name']}` characters {e['start_offset']}:{e['end_offset']}:",'','```text',e['quote'],'```','']
    (DIR/'REVIEW.md').write_text('\n'.join(lines))
    print(json.dumps(comparison,indent=2))
    for key in ('answer_correctness','original_rubric_correctness','faithfulness','citation_support','citation_coverage','appropriate_abstention','generation_seconds','generation_first_delta_seconds','token_usage','reliability'):
        print(key,m[key])
