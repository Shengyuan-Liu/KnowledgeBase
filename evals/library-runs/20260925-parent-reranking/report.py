"""Publish controlled coverage changes and an explicit limited manual answer review."""
import json
from pathlib import Path
from statistics import mean
from evals import metrics
from evals.evaluate import digest,read_jsonl,timestamp,write_json
DIR=Path(__file__).parent
BASE=DIR.parent/'20260925T002400Z-semantic-acceptance'

if __name__=='__main__':
    assert not (DIR/'comparison.json').exists()
    comparison={}
    for strategy in ('parent_child','semantic'):
        control={r['case_id']:r for r in read_jsonl(DIR/f'{strategy}-child-4096.jsonl')}
        for unit in ('child','parent'):
            for budget in (4096,6144):
                label=f'{strategy}-{unit}-{budget}'
                rows=read_jsonl(DIR/f'{label}.jsonl')
                assert len(rows)==24 and all(r['status']=='ok' for r in rows)
                comparison[label]={'evidence_tokens_mean':mean(r['retrieval']['evidence_tokens'] for r in rows),
                    'coverage':json.loads((DIR/f'{label}-summary.json').read_text())['metric_inventory']['final_evidence_coverage'],
                    'rerank_seconds':metrics.timing([r['retrieval']['rerank_seconds'] for r in rows]),
                    'score_origins':sorted({r['scores_origin'] for r in rows}),
                    'case_changes':[{'case_id':r['case_id'],'before':control[r['case_id']]['coverage'],'after':r['coverage']} for r in rows if r['coverage']!=control[r['case_id']]['coverage']]}
    write_json(DIR/'comparison.json',comparison)
    cases={c['id']:c for c in json.loads((BASE/'cases.json').read_text())}
    answers=read_jsonl(DIR/'generation-answers.jsonl');reviews=[]
    for row in answers:
        case=cases[row['case_id']];after=row['variant']=='semantic-parent-6144';work=row['case_id']=='msds-working-enrollment'
        phrases=(['suggests that if you have a full-time job','Evening classes are not guaranteed.', 'No, continuous enrollment' if after else 'The provided source does not mention'] if work else
            ['The admissions FAQ explains' if after else 'The admissions FAQ was referenced',
             'The Industry Concentration requires' if after else 'The Industry Concentration page states',
             'The Industry Concentration page specifically advises' if after else 'The Industry Concentration page advises'])
        source_ids=([1,1,2] if after else [1,1,None]) if work else ([4,1,1] if after else [None,4,4])
        points=[]
        for index,(phrase,identity) in enumerate(zip(phrases,source_ids),1):
            line=next(line for line in row['answer'].splitlines() if phrase in line)
            evidence=[]
            if identity:
                source=next(s for s in row['sources'] if s['source_id']==identity)
                for span in case['evidence']:
                    if index in span['supports_answer_points'] and span['file']==source['file_name']:
                        left,right=span['start_offset']-source['start_offset'],span['end_offset']-source['start_offset']
                        assert 0<=left<right<=len(source['text'])
                        quote=source['text'][left:right];assert quote==span['quote']
                        evidence.append({'source_id':identity,'start_offset':span['start_offset'],'end_offset':span['end_offset'],'quote':quote})
                assert evidence and f'[{identity}]' in line
            points.append({'point':index,'reference':case['expected_answer_points'][index-1],'answer_quote':line,
                'correctness':2 if identity else 0,'answered':bool(identity),'supporting_citation':bool(identity),'evidence':evidence,
                'reason':'Required fact is answered with the stated qualification and supporting source.' if identity else 'Answer explicitly cannot supply this fact because the necessary excerpt is missing.'})
        reviews.append({'case_id':row['case_id'],'variant':row['variant'],'reviewer':'Codex','method':'Manual expected-point review of all four answers, exact supplied source spans, unchanged benchmark points. Not v11 or independent human review.',
            'answer_sha256':digest(row['answer'].encode()),'points':points,
            'partial_refusal':not after,'retrieval_justifies_refusal':not after,
            'additional_findings':(['The control incorrectly calls the FAQ excerpt merely a reference with no direct text; it is the FAQ referenced-links region. Its expansion of CPT is not supplied in those excerpts.'] if not work and not after else
                ['Recommendation remains attributed as a recommendation, not a program-wide maximum; quoted evening and summer statements match supplied text.'] if work and after else
                ['Both timing statements retain source attribution; no claim that one overrides the other.'] if not work else ['Missing summer fact is acknowledged.'])})
    write_json(DIR/'manual-review.json',reviews)
    calls=read_jsonl(DIR/'generation-calls.jsonl');run=json.loads((DIR/'generation-run.json').read_text())
    output={}
    for variant in ('semantic-child-4096','semantic-parent-6144'):
        selected=[r for r in reviews if r['variant']==variant];rows=[r for r in answers if r['variant']==variant];observed=[c for c in calls if c['variant']==variant]
        points=[p for r in selected for p in r['points']]
        inventory={k:metrics.missing('No new retrieval, embedding, ingestion, load, or lifecycle measurement in this generation-only probe.',False)
                   for k in json.loads(Path('evals/check-runs/20260924-judge-calibration/backend-6.json').read_text())['metric_inventory']}
        for key in ('faithfulness','answer_relevance','citation_support','citation_coverage'):
            inventory[key]=metrics.missing('This limited manual protocol scores required reference points and inspects additional failures; no exhaustive atomic-claim/citation inventory or independently frozen full-answer rubric. Point support is not full-answer quality.')
        for key in ('recall_at_k','precision_at_k','hit_rate_at_k','mrr_at_k','ndcg_at_k','final_evidence_coverage'):
            inventory[key]=json.loads((DIR/f'{variant}-summary.json').read_text())['metric_inventory'][key]
            inventory[key]['origin']='Earlier full 24-case offline frozen-route retrieval comparison; not remeasured by generation.'
        inventory['answer_correctness']=metrics.measured(sum(p['correctness']/2 for p in points)/len(points),'fraction',len(points),'Manual expected-point correctness, 0/1/2 normalized, six points across two questions; Codex, not independent.','manual-review.json')
        inventory['answer_completeness']=metrics.measured(sum(p['answered'] for p in points)/len(points),'fraction',len(points),'Required facts actually supplied, not just mentioned as missing; differs from v11 attempted-point completeness.','manual-review.json')
        inventory['abstention']={'appropriate_on_unanswerable':metrics.missing('Both probe questions are answerable.',False),
            'partial_refusal_on_answerable':metrics.measured(sum(r['partial_refusal'] for r in selected)/len(selected),'fraction',len(selected),'Both control refusals reflect missing retrieved evidence; new contexts remove the gap.','manual-review.json'),
            'incorrect_despite_sufficient_context':metrics.measured(0,'fraction',len(selected),'No refusal contradicting supplied evidence among required points; distinguish retrieval-caused refusal.','manual-review.json')}
        inventory['first_answer_delta_latency']=metrics.timing([r['generation_first_delta_seconds'] for r in rows]);inventory['first_answer_delta_latency']['method']='Generation stream start to first nonempty delta; excludes HTTP RAG service and retrieval.'
        inventory['complete_response_latency']=metrics.missing('No end-to-end HTTP RAG request. Generation completion is recorded separately as stage latency.')
        inventory['stage_latency']={'generation_completion':metrics.timing([r['generation_seconds'] for r in rows]),'scope':'Provider generation only, no queue/load study; two requests per variant, alternating control/treatment by question.'}
        inventory['token_usage_and_cost']={'status':'measured','value':{k:sum(c['usage'][k] for c in observed) for k in ('input_tokens','output_tokens','total_tokens')},'unit':'tokens','n':2,'artifact':'generation-calls.jsonl','billed_cost':metrics.missing('Actual provider billing unavailable.')}
        inventory['reliability']=metrics.measured({'success':sum(r['status']=='ok' for r in rows),'error':sum(r['status']!='ok' for r in rows),'timeout':0,'retry':0},'requests',2,'All planned requests retained; SDK retries disabled.','generation-answers.jsonl')
        inventory['concurrency_and_throughput']=metrics.measured({'concurrency':1,'all_variants_wall_seconds':run['wall_seconds'],'all_variants_requests_per_second':4/run['wall_seconds']},'requests/second',4,'Sequential four-request generation probe; combined population, not per-variant load capacity.','generation-run.json')
        output[variant]={'metric_inventory':inventory,'resolved_models':sorted({c['resolved_model'] for c in observed})}
    write_json(DIR/'generation-summary.json',output)
    print('192 retrieval replays and 4 generation answers recorded; 6 expected points reviewed per variant.')
