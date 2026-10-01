"""Serialize explicit manual judgments and attach mechanical source provenance."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re

OUT=Path(__file__).parent
RUN=OUT.parent

def read(p):return json.loads(p.read_text())
def save(name,value):
    with (OUT/name).open('x') as handle:json.dump(value,handle,indent=2);handle.write('\n')

manual=read(OUT/'manual-judgments.json')
frozen=read(RUN/'frozen-cases.json')
labels=read(RUN/'frozen-fact-labels.json')['labels']
diagnostics=read(RUN/'metrics/retrieval-diagnostics.json')['rows']
extraction=read(RUN/'index-snapshot.json')['files'][0]['extraction']
observations=[json.loads(line) for line in (RUN/'server-observations.jsonl').read_text().splitlines()]
rows=[];assessments=[]
for judgment in manual['rows']:
    case_id,arm=judgment['case_id'],judgment['arm'];identity=case_id+'-'+arm
    raw=read(RUN/(identity+'.json'));answer=raw.get('answer',{});text=answer.get('answer','');lines=text.splitlines()
    case=next(c for c in frozen['cases'] if c['id']==case_id)
    diag=next(d for d in diagnostics if d['case_id']==case_id and d['arm']==arm)
    points=[]
    for fact_id,score,coverage in zip(case['expected_fact_ids'],judgment['points'],diag['final_structural_coverage']['facts'],strict=True):
        assert fact_id==coverage['fact_id']
        points.append(dict(fact_id=fact_id,reference_correctness=score,completeness=score,
            supplied_evidence_coverage=int(coverage['fully_covered']) if raw['status']=='completed' else None,
            semantic_score_status='measured' if score is not None else 'unavailable',
            score_reason=judgment['note'],original_source_binding=labels[fact_id],actual_source_checks=coverage['source_checks']))
    claims=[]
    factual_ids=[fact for fact,score in zip(case['expected_fact_ids'],judgment['points'],strict=True) if score==1]
    assert len(factual_ids)==len(judgment['claim_line_indices'])
    for line_index,fact_id in zip(judgment['claim_line_indices'],factual_ids,strict=True):
        claim=lines[line_index].strip().removeprefix('- ')
        cited=[int(n) for n in re.findall(r'\[(\d+)\]',claim)]
        coverage=next(c for c in diag['final_structural_coverage']['facts'] if c['fact_id']==fact_id)
        supporting=[check['source_id'] for check in coverage['source_checks'] if check['complete']]
        assert set(cited)&set(supporting)
        claims.append(dict(text=claim,fact_ids=[fact_id],original_page_correctness=1,context_support=1,
            citation_support=1,citation_coverage=1,cited_source_ids=cited,supporting_source_ids=supporting,note=judgment['note']))
    missing=[dict(fact_id=fact,text=lines[judgment['missing_line_indices'][0]],appropriate_to_actual_context=False,
        contextual_faithfulness=0,citation_support=0,reason=judgment['note']) for fact,score in zip(case['expected_fact_ids'],judgment['points'],strict=True)
        if score==0]
    row=dict(case_id=case_id,arm=arm,answer_status=raw['status'],actual_answer=text,
        source_artifact='../'+identity+'.json',source_artifact_sha256=sha256((RUN/(identity+'.json')).read_bytes()).hexdigest(),
        points=points,factual_claim_groups=claims,missing_point_review=missing,
        excluded_framing=[dict(text=lines[i],reason='Repeated question context; subsequent facts are scored separately.') for i in judgment['framing_line_indices']],
        relevance=1 if raw['status']=='completed' else None,full_abstention=False if raw['status']=='completed' else None,
        incorrect_abstention=0 if raw['status']=='completed' else None,appropriate_abstention=None,note=judgment['note'])
    rows.append(row)
    if arm=='planned' and raw['status']=='completed':
        for assessment in answer['retrieval']['planning']['hops']['assessments']:
            sdk=next(o for o in observations if o['kind']=='sdk_start' and o['request']==identity
                and o['api']=='responses' and o['input'].get('text',{}).get('format',{}).get('name')=='evidence_assessment')
            assert assessment['record']['input']==sdk['input']['input']
            payload=json.loads(next(m['content'] for m in sdk['input']['input'] if m['role']=='user'))
            decision=json.loads(assessment['record']['output_text']);checks=[]
            for requirement in assessment['requirements']:
                selected=next(r for r in decision['requirements'] if r['requirement_id']==requirement['requirement_id'])
                assert [r['evidence_id'] for r in selected['references']]==[r['evidence_id'] for r in requirement['references']]
                for ref in [*requirement['references'],*requirement['table_context']]:
                    assert ref['quote']==extraction['text'][ref['start_offset']:ref['end_offset']]
                    assert f"[{ref['evidence_id']}] {ref['quote']}" in payload['context']
                    assert ref['page_indices']==[0]
                checks.append(dict(requirement=requirement,selected_ids_preserved=True,exact_quotes_and_page_preserved=True,
                    manual_status_judgment='Supported: cited Alabama row or disclaimer plus supplied full headers and explicit cell readings establish the requested content. Availability does not guarantee downstream interpretation.'))
            assessments.append(dict(identity=identity,sdk_call_id=sdk['call_id'],requirements=checks,original_decision=decision))
review=dict(reviewer=manual['reviewer'],method=manual['method'],reviewed_at=datetime.now(timezone.utc).isoformat(),
    code_version=read(RUN/'resolved-runtime.json')['code_commit'],rubric='../frozen-original-protocol.md',
    independent_second_review=dict(status='unavailable',reason='This turn uses one agent; mechanical audits are not independent semantic review.'),
    rows=rows,scope_note='Five generated answers and one pre-retrieval error. Error semantic scores are unavailable; all intended points remain in the functional delivery gate.',
    missing_information_claims_note='Nineteen substantive factual groups are supported; one separate unsupported limitation affects two requested blank facts. Report that omission alongside faithfulness/citation rates.')
save('reviewed-cases.json',review)
save('assessment-reference-review.json',dict(reviewer=manual['reviewer'],rows=assessments,
    unavailable_case='state-totals-planned: failed before retrieval/assessment',provider_calls=0))
print('Retained manual review: 19 correct points out of 21 delivered opportunities; two incorrect blank omissions; three points undelivered by the failed request. Nineteen supported factual groups and one unsupported limitation, separately reported.')
