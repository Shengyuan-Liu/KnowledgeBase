"""Consolidate all twenty metrics by frozen population; never fill missing values with zero."""
from collections import Counter,defaultdict
from datetime import datetime
from pathlib import Path
import json,math,statistics
from analyze import distribution
from labels import covered
from record_check import METRICS
ROOT=Path(__file__).parent
read=lambda p:json.loads(p.read_text())
def write(name,data):
 with (ROOT/name).open('x') as f:json.dump(data,f,indent=2);f.write('\n')
obs=[json.loads(l) for l in (ROOT/'server-observations.jsonl').read_text().splitlines()]
snapshot=read(ROOT/'heldout-index-snapshot.json');chunks={c['chunk_id']:c for d in snapshot['files'] for c in d['chunks']}
labels=read(ROOT/'frozen-labels.json');page_labels=read(ROOT/'heldout-page-labels.json')['facts']
original=read(Path('evals/materials/pdf-v2-candidate-20261001/references.json'))
casefacts={c['case_id']:c['fact_ids'] for c in original['cases']}
for fact in read(Path('evals/materials/pdf-v2-closeout-dependency/protocol.json'))['facts']:
 doc=next(d for d in snapshot['files'] if d['file']['file_name']==fact['file']);start=doc['extraction']['text'].index(fact['quote']);labels[fact['id']]={'anchors':[{'anchor':fact['quote'],'spans':[{'file_id':doc['file']['file_id'],'start':start,'end':start+len(fact['quote'])}]}]}
casefacts['unknown-laboratory']=['lab_bridge','lab_interval']
heldout=read(ROOT/'heldout-review.json');ablation=read(ROOT/'ablation-review.json')
for c in read(Path('evals/materials/pdf-v2-closeout-heldout/protocol.json'))['questions']:casefacts[c['id']]=c['facts']

def relevance(case):
 facts=casefacts[case]
 if not facts:return None
 if facts[0] in labels:
  return {i for i,c in chunks.items() if any(covered([c],labels[f]) for f in facts)}
 relevant=set()
 for f in page_labels:
  if f['id'] not in facts:continue
  for i,c in chunks.items():
   if c['file_id']==f['file_id'] and any(c['start_offset']<e and s<c['end_offset'] for s,e in f['page_spans']):relevant.add(i)
 return relevant

def ranking(ids,relevant,k):
 if relevant is None:return None
 if not relevant:return {'status':'unavailable','reason':'No relevant units mapped; not scored as zero.'}
 selected=list(dict.fromkeys(ids))[:k];binary=[int(i in relevant) for i in selected];ideal=sum(1/math.log2(i+2) for i in range(min(k,len(relevant))))
 return {'K':k,'Recall@K':sum(binary)/len(relevant),'Precision@K':sum(binary)/k,'Hit Rate@K':int(any(binary)),'MRR':next((1/(i+1) for i,b in enumerate(binary) if b),0),'NDCG@K':sum(v/math.log2(i+2) for i,v in enumerate(binary))/ideal,'relevant_units':len(relevant),'ids':selected,'binary':binary}

def operational(rows,observations):
 requestids={r['request']['request_id'] for r in rows};events=[o for o in observations if o['request'] in requestids];starts={o['call_id']:o for o in events if o['kind']=='sdk_start'};calls=[];stage=defaultdict(list);usage=defaultdict(lambda:dict(calls=0,input_tokens=0,output_tokens=0,total_tokens=0))
 for e in events:
  if e['kind']=='stage':stage[e['stage']].append(e['seconds'])
  if e['kind'] not in ['sdk_complete','sdk_stream_terminal','sdk_error']:continue
  start=starts[e['call_id']];out=e.get('result') or e.get('event',{}).get('response') or {};role='embedding' if start['api']=='embeddings' else start['input'].get('text',{}).get('format',{}).get('name','generation');stage[role].append(e['seconds']);u=out.get('usage');calls.append({'request':e['request'],'call_id':e['call_id'],'role':role,'seconds':e['seconds'],'model':out.get('model'),'usage':u,'terminal_kind':e['kind'],'error':e.get('error_type')})
  if u:
   usage[role]['calls']+=1;usage[role]['input_tokens']+=u.get('input_tokens',u.get('prompt_tokens',0));usage[role]['output_tokens']+=u.get('output_tokens',0);usage[role]['total_tokens']+=u['total_tokens']
 for role,u in usage.items():
  if role=='embedding':u['output_tokens']=None;u['output_status']='not_applicable: vectors, not generated tokens'
 for r in rows:
  d=r.get('answer',{}).get('retrieval',{})
  for name in ['scope_seconds','embedding_seconds','rerank_seconds','packing_seconds','retrieval_seconds']:
   if d.get(name) is not None:stage[name].append(d[name])
 elapsed=sum(r['complete_response_seconds'] for r in rows);times=[datetime.fromisoformat(r['at']).timestamp() for r in rows];wall=max(t+r['complete_response_seconds'] for t,r in zip(times,rows))-min(times)
 return {'first_delta':distribution([r['first_answer_delta_seconds'] for r in rows if r['first_answer_delta_seconds'] is not None]),'completion':distribution([r['complete_response_seconds'] for r in rows]),'stages':{k:distribution(v) for k,v in stage.items()},'calls':calls,'usage':dict(usage),'provider_starts':len(starts),'provider_terminals':len(calls),'provider_errors':sum(c['terminal_kind']=='sdk_error' for c in calls),'provider_timeouts':sum('Timeout' in (c['error'] or '') for c in calls),'retries':0,'requests':dict(Counter(r['status'] for r in rows)),'active_request_seconds':elapsed,'wall_interval_seconds':wall,'active_sequential_completion_rate':sum(r['status']=='completed' for r in rows)/elapsed,'wall_completion_rate':sum(r['status']=='completed' for r in rows)/wall}

def measurement(name,rows,reviews,observations=obs):
 operations=operational(rows,observations);metrics={};rankings=[]
 for r in rows:
  d=r['answer']['retrieval'];case=r['case_id'];rel=relevance(case);sources=r['answer']['sources'];ids=[i for s in sources for i in s.get('matched_child_ids',[])];selected=ranking(ids,rel,5);query=[]
  trace=(d.get('planning') or {}).get('trace') or {};runs=trace.get('runs') or [{'text':r['request']['question'],'result':{'diagnostics':d}}]
  for run in runs:
   q=run['result']['diagnostics'];stages={}
   for stage in ['vector_matches','bm25_matches','fused_matches']:
    for k in [5,20]:stages[stage+f'@{k}']=ranking([x['chunk_id'] for x in q.get(stage,[])],rel,k)
   for k in [5,20]:stages[f'rerank@{k}']=ranking([x['chunk_id'] for x in (q.get('rerank') or {}).get('matches',[])],rel,k)
   query.append({'text':run['text'],'stage_metrics':stages})
  rankings.append({'case_id':case,'final_supplied_child_order':selected,'queries':query,'evidence_tokens':d['evidence_tokens'],'budget_exclusions':d['excluded']})
 def measured(key,value,unit,count,method,artifact='measurement.json',aggregation='Explicit population counts or unweighted case macro'):
  metrics[key]={'status':'measured','value':value,'unit':unit,'sample_count':count,'population':name,'method':method,'aggregation':aggregation,'artifact':artifact}
 def unavailable(key,reason):metrics[key]={'status':'unavailable','value':None,'unit':None,'reason':reason,'sample_count':len(rows),'population':name,'method':'Not available','aggregation':'none','artifact':'Raw answer and source artifacts'}
 scored=[r['final_supplied_child_order'] for r in rankings if r['final_supplied_child_order'] and 'status' not in r['final_supplied_child_order']]
 labelkind='Frozen full-anchor child relevance; equivalent passages not exhaustively labeled' if name!='heldout' else 'Frozen original-page relevance mapped before answers; child intersects a gold page, a coarse diagnostic rather than semantic relevance'
 for key in METRICS[:5]:measured(key,{'macro':statistics.mean(s[key] for s in scored),'K':5,'available_queries':len(scored)},'ratio',len(scored),labelkind+'. Final supplied children in source order, deduplicated; precision denominator K even if fewer hits; MRR truncated at K, binary/log2 NDCG. Candidate/fusion/reranking K=5/20 kept separately.')
 points=[p for r in reviews for p in r['expected_points']];claims=[*points,*[p for r in reviews for p in r.get('additional_claims',[])]]
 for key,field,units in [('Final evidence coverage','supplied_semantic_evidence',points),('Answer correctness','correct',points),('Answer completeness','complete',points),('Faithfulness','faithful',claims),('Citation support','citation_supported',claims),('Citation coverage','citation_covered',claims)]:
  measured(key,{'passed':sum(x.get(field,True) for x in units),'total':len(units)},'review units',len(units),'Codex original-page and exact supplied-context review; expected facts and additional substantive claim groups kept separately. Contradictory drafts retained. Valid citation IDs alone do not establish support.','review.json / ablation-review.json / heldout-review.json')
 measured('Answer relevance',{'passed':sum(r.get('relevant',True) for r in reviews),'total':len(reviews)},'cases',len(reviews),'Question focus and absence of irrelevant/contradictory additions.','Semantic review artifacts')
 measured('Abstention',{'incorrect_full_refusal':sum(r['answer']['answer'].startswith('There is not enough') and bool(casefacts[r['case_id']]) for r in rows),'answerable_or_partial_count':sum(bool(casefacts[r['case_id']]) for r in rows),'appropriate_full_refusal':sum(r['answer']['answer'].startswith('There is not enough') and not casefacts[r['case_id']] for r in rows),'unanswerable_count':sum(not casefacts[r['case_id']] for r in rows),'partial_gap_correct':sum(r.get('gap_disclosure_correct',True) for r in reviews if r['case_id'] in ['retriever-training-restricted','transformer-energy-partial']),'partial_count':sum(r['case_id'] in ['retriever-training-restricted','transformer-energy-partial'] for r in reviews),'incorrect_partial_case_ids':[r['case_id'] for r in reviews if any(not p['complete'] for p in r['expected_points'])]},'cases',len(rows),'Separate no-gold, partial and positive populations; a zero denominator means not applicable, not a successful abstention rate.')
 for key,field in [('First-answer-delta latency','first_delta'),('Complete-response latency','completion')]:measured(key,operations[field],'seconds',len(rows),'HTTP POST to nonempty answer delta / SSE end. Network and queue included; model startup and ingestion excluded. Linear-interpolated percentiles. No repeated warm-run/load claim.')
 measured('Stage latency',{'distributions':operations['stages'],'missing':{'search_and_fusion':'unavailable: no isolated timer','provider_queue':'unavailable: included but not isolated'}},'seconds',None,'SDK and product perf_counter timers; overlap, do not sum. Reranker MPS, other retrieval CPU.')
 measured('Token usage and cost',{'by_role':operations['usage'],'resolved_models':sorted({c['model'] for c in operations['calls'] if c['model']}),'billed_cost':{'status':'unavailable','reason':'Provider SDK reports usage, not currency; no billing API used.'},'local_compute':'MPS reranker; CPU parsing/search. No invented monetary equivalent.'},'tokens',len(operations['calls']),'Actual provider usage for this request cohort; query and generation totals separate.')
 measured('Reliability',{k:operations[k] for k in ['requests','provider_starts','provider_terminals','provider_errors','provider_timeouts','retries']},'counts',len(rows),'Includes every request and provider attempt in this cohort; separate semantic gates in review.')
 measured('Concurrency and throughput',{'concurrency':1,'active_request_seconds':operations['active_request_seconds'],'active_sequential_completion_rate':operations['active_sequential_completion_rate'],'wall_interval_seconds':operations['wall_interval_seconds'],'wall_completion_rate':operations['wall_completion_rate']},'requests/second',len(rows),'Sequential throughput only; A/B/C cases are interleaved, so the per-arm wall interval includes other arms. Active-time rate excludes that gap and is labeled separately. Neither is production capacity.')
 metrics['Ingestion and index']={'status':'not_applicable','value':None,'unit':None,'reason':'This answer cohort reuses an index; ingestion/lifecycle measurements are recorded in the run-level section.','sample_count':0,'population':name,'method':'No ingestion inside answering requests','aggregation':'none','artifact':'ingest-*.json; lifecycle-result.json; final-index-check.json'}
 assert set(metrics)==set(METRICS)
 return {'metric_inventory':metrics,'rankings':rankings,'operations':operations}

cohorts={}
matched=read(ROOT/'review.json')['cases'];cohorts['matched']=measurement('matched',[read(ROOT/(r['case_id']+'-planned.json')) for r in matched],matched)
for arm in 'ABCD':
 reviews=[r for r in ablation['cases'] if r['arm']==arm];cohorts['ablation-'+arm]=measurement('ablation-'+arm,[read(ROOT/'ablation'/f"{r['case_id']}--{arm}.json") for r in reviews],reviews)
cohorts['heldout']=measurement('heldout',[read(ROOT/'heldout'/f"{r['case_id']}--D.json") for r in heldout['cases']],heldout['cases'])
# Account for all paid work, including ingestion, shadow assessments and browser calls.
starts={o['call_id']:o for o in obs if o['kind']=='sdk_start'};terminal=[o for o in obs if o['kind'] in ['sdk_complete','sdk_stream_terminal','sdk_error']]
allusage=defaultdict(lambda:dict(calls=0,input_tokens=0,output_tokens=0,total_tokens=0))
for o in terminal:
 s=starts[o['call_id']];result=o.get('result') or o.get('event',{}).get('response') or {};u=result.get('usage');role=('ingestion_embedding' if s['request'].startswith('ingest-') or s['request']=='unlabeled' else 'query_embedding') if s['api']=='embeddings' else s['input'].get('text',{}).get('format',{}).get('name','generation')
 if u:
  t=allusage[role];t['calls']+=1;t['input_tokens']+=u.get('input_tokens',u.get('prompt_tokens',0));t['output_tokens']+=u.get('output_tokens',0);t['total_tokens']+=u['total_tokens']
for role,t in allusage.items():
 if role.endswith('embedding'):t['output_tokens']=None
runtime=read(ROOT/'resolved-runtime.json')
ingestions=[read(p) for p in ROOT.glob('ingest-*.json')]
report={'code_commit':runtime['code_commit'],'reviewer':'Codex model; no independent human validation','cohorts':cohorts,'runtime':{'reranker':runtime['reranker'],'device':runtime['device'],'packages':runtime['packages'],'settings':runtime['settings']},'total_provider_work':{'starts':len(starts),'terminals':len(terminal),'errors':sum(o['kind']=='sdk_error' for o in terminal),'timeouts':sum('Timeout' in o.get('error_type','') for o in terminal),'retries':0,'usage_by_role':dict(allusage),'billed_currency':{'status':'unavailable','reason':'No actual billing evidence.'},'note':'Unique events counted once. D outcomes reused across matched/ablation are not double-billed. Shadow calls and real browser lifecycle calls are included; offline tests have mocked providers. Unlabeled browser embeddings include both ingestion and query; raw input and vector counts distinguish them.'},'ingestion_and_index':{'new_heldout_uploads':ingestions,'new_heldout_seconds':distribution([x['seconds'] for x in ingestions]),'files_before_lifecycle':len(snapshot['files']),'pages_before_lifecycle':sum(len(d['extraction']['pages']) for d in snapshot['files']),'children':sum(len(d['chunks']) for d in snapshot['files']),'parents':sum(len(d['parents']) for d in snapshot['files']),'bytes_before_lifecycle':snapshot['index_bytes'],'lifecycle':read(ROOT/'lifecycle-completion.json'),'update':{'status':'not_applicable','reason':'No in-place update feature; delete/reupload is the supported workflow.'},'isolated_vector_bytes':{'status':'unavailable','reason':'Directory total includes PDFs, SQLite, Chroma and history.'}},'shadow_assessment':ablation['shadow_C'],'limitations':['One pass, small populations. No statistical or independent-human generalization claim.','A/B/C controls preserve failed/unsupported answers and invalid citation markers.','No claim that supplementary search improves coverage on this workload: the one restricted gap is outside allowed scope.','Candidate labels are incomplete anchors or coarse pages; semantic context/answer review is separate.','Provider queue, isolated search/fusion and billed currency unavailable.','Browser lifecycle ran alongside offline checks; its elapsed time is not an isolated production latency estimate.']}
write('measurement.json',report)
# The initial matched attempt has the same full policy inventory and retained failed citation gate.
old=ROOT.parent/'20261001-v2-closeout-matched';before=read(old/'review.json')['cases'];oldobs=[json.loads(l) for l in (old/'server-observations.jsonl').read_text().splitlines()]
initial=measurement('initial-matched',[read(old/(r['case_id']+'-planned.json')) for r in before],before,oldobs)
initial['dependency_failure']={'artifact':'dependency/unknown-laboratory-planned.json','case_gate':False,'facts_delivered':1,'facts_expected':2,'status':'completed but incomplete answer'}
initial['scope_note']='The matched cohort metrics cover its six requests; two synthetic document uploads and the failed dependency request are retained in SDK logs and their command record, with separate operational details below.'
dep=read(old/'dependency/unknown-laboratory-planned.json');initial['additional_work_operations']=operational([dep],oldobs);initial['ingestions']=[read(p) for p in old.glob('ingest-*.json')]
with (old/'measurement.json').open('x') as f:json.dump(initial,f,indent=2);f.write('\n')
print('All 20 metrics recorded per cohort, plus raw per-query K=5/20, unique provider usage and lifecycle results.')
for name,c in cohorts.items():print(name,'first_delta_mean',round(c['operations']['first_delta']['mean'],3),'complete_mean',round(c['operations']['completion']['mean'],3),'provider_calls',c['operations']['provider_starts'])
print('Unique provider calls',len(starts),'total tokens',sum(u['total_tokens'] for u in allusage.values()))
