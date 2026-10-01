"""Compare fixed selected candidates and exact packed spans; no generated answers."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import statistics

from replay import ROOT, LIVE, FILES, CHUNKS, CASES
from record_check import METRICS

LABELS = json.loads((LIVE/'anchor-labels.json').read_text())
BEFORE = json.loads((ROOT/'before.json').read_text())
AFTER = json.loads((ROOT/'after-2.json').read_text())
assert BEFORE['frozen_sha256'] == AFTER['frozen_sha256']


def spans(result):
    result_spans=[]
    for hit in result['chunks']:
        chunk=hit['chunk']
        result_spans.append(dict(file_id=chunk['file_id'],start=chunk['start_offset'],end=chunk['end_offset']))
        for extra in hit['pdf']['supplements']:
            result_spans.append(dict(file_id=chunk['file_id'],start=extra['start_offset'],end=extra['end_offset']))
    return result_spans


def contains(source, target):
    return source['file_id']==target['file_id'] and source['start']<=target['start'] and target['end']<=source['end']


def facts_covered(row):
    actual=spans(row['result'])
    return {f: int(all(any(contains(s, target) for s in actual for target in anchor['spans'])
                       for anchor in LABELS[f]['anchors'])) for f in row['facts']}


def candidate_metrics(row):
    identities=row['selected_ids'][:5]
    ids=[dict(file_id=CHUNKS[i]['file_id'],start=CHUNKS[i]['start_offset'],end=CHUNKS[i]['end_offset']) for i in identities]
    def relevant(chunk):
        return any(chunk['file_id']==s['file_id'] and chunk['start'] < s['end'] and s['start'] < chunk['end']
                   for f in row['facts'] for a in LABELS[f]['anchors'] for s in a['spans'])
    binary=[int(relevant(c)) for c in ids]
    coverage={f:int(all(any(contains(c,s) for c in ids for s in a['spans']) for a in LABELS[f]['anchors'])) for f in row['facts']}
    ideal=min(5,sum(relevant(dict(file_id=c['file_id'],start=c['start_offset'],end=c['end_offset'])) for c in CHUNKS.values()))
    idcg=sum(1/math.log2(i+2) for i in range(ideal))
    return {'Recall@K':statistics.mean(coverage.values()),'Precision@K':sum(binary)/5,
            'Hit Rate@K':int(any(binary)),'MRR':next((1/(i+1) for i,b in enumerate(binary) if b),0),
            'NDCG@K':sum(b/math.log2(i+2) for i,b in enumerate(binary))/idcg if idcg else 0}


def distribution(values):
    values=sorted(values)
    def percentile(p):
        i=(len(values)-1)*p;n=int(i)
        return values[n]+(values[min(n+1,len(values)-1)]-values[n])*(i-n)
    return dict(n=len(values),mean=statistics.mean(values),p50=percentile(.5),p95=percentile(.95),unit='seconds',percentile='linear')


def metric(value,unit,n,population,method,artifact,aggregation='macro mean'):
    return dict(status='measured',value=value,unit=unit,sample_count=n,population=population,
                method=method,aggregation=aggregation,artifact=artifact)


rows=[]
for before,after in zip(BEFORE['rows'],AFTER['rows'],strict=True):
    assert (before['case_id'],before['arm'],before['selected_ids'])==(after['case_id'],after['arm'],after['selected_ids'])
    for row in [before,after]:
        assert row['result']['diagnostics']['evidence_tokens'] <= 4096
        for hit in row['result']['chunks']:
            text=FILES[hit['chunk']['file_id']]['extraction']['text']
            assert hit['chunk']['text']==text[hit['chunk']['start_offset']:hit['chunk']['end_offset']]
            for extra in hit['pdf']['supplements']:
                assert extra['text']==text[extra['start_offset']:extra['end_offset']]
    b,a=facts_covered(before),facts_covered(after)
    rows.append(dict(case_id=before['case_id'],arm=before['arm'],question=before['question'],
        selected_ids=before['selected_ids'],candidate_metrics=candidate_metrics(before) if before['facts'] else None,
        before_covered=b,after_covered=a,improved=[f for f in b if a[f]>b[f]],regressed=[f for f in b if a[f]<b[f]],
        before_tokens=before['result']['diagnostics']['evidence_tokens'],after_tokens=after['result']['diagnostics']['evidence_tokens']))

inventory={m:dict(status='not_applicable',value=None,unit=None,sample_count=None,population='Offline fixed-candidate packing replay',
    method='Not exercised',aggregation='none',artifact='before.json; after-2.json',
    reason='No provider requests, answer generation, ingestion, lifecycle or load experiment; this replay compares only packing and supplied context.') for m in METRICS}
for m in METRICS[:5]:
    inventory[m]=metric(statistics.mean(r['candidate_metrics'][m] for r in rows if r['candidate_metrics']),
        'ratio',28,'14 fact-bearing questions in two modes; same K=5 selected children before/after',
        'Frozen original-page anchor labels; selected stage fixed by design. Recall uses complete fact anchor sets; precision/binary ranking uses any anchor intersection and denominator 5; incomplete labels. No-gold cases excluded.',
        '../../library-runs/20260927-v2-pdf-live/anchor-labels.json')
for phase in ['before','after']:
    values=[statistics.mean(r[phase+'_covered'].values()) for r in rows if r[phase+'_covered']]
    if phase=='before':coverage={}
    coverage[phase]=statistics.mean(values)
inventory['Final evidence coverage']=metric(coverage,'ratio',28,'Same 28 fact-bearing mode/question pairs; 72 fact instances',
    'Macro mean of fully covered original-page anchor sets in actual packed body/supplement spans. Exact canonical offsets; partial sets receive 0, missing parser anchors remain misses. This is an evidence diagnostic, not answer correctness.',
    'comparison-2.json#rows')
inventory['Stage latency']=metric({'before':distribution([r['seconds'] for r in BEFORE['rows']]),'after':distribution([r['seconds'] for r in AFTER['rows']])},
    'seconds',32,'Each local fixed-candidate set once per version',
    'perf_counter across PDF evidence attachment and packing; parse/index/provider/network/model loading and queue waiting excluded. First call includes local tokenizer cache initialization. CPU-only developer-machine measurement, not production response latency.',
    'before.json; after-2.json','mean/P50/P95')
inventory['Token usage and cost']=metric({'before_evidence_tokens':[r['before_tokens'] for r in rows],'after_evidence_tokens':[r['after_tokens'] for r in rows],
    'provider_usage':{'status':'not_applicable','value':None,'reason':'No API call or generated answer.'},
    'billed_cost':{'status':'not_applicable','value':None,'reason':'No paid workload.'}},'local cl100k_base context tokens',32,
    'Actual rendered source context, including metadata, headers, warnings and preceding text','Count build_context() under the same 4096 budget. Local compute has no measured monetary cost.',
    'before.json; after-2.json','per-case values')
inventory['Reliability']=metric({'before_completed':32,'after_completed':32,'errors':0,'retries':0,'exact_body_and_supplement_spans_verified':True},
    'counts',64,'Offline packing calls only; initial harness construction failure separately retained in before-record.log',
    'Completion, fixed selection, budget and canonical-slice assertions; no network reliability claim.','before.json; after-2.json','counts')
result=dict(timestamp=datetime.now(timezone.utc).isoformat(),scope='Offline packing component comparison; no live evaluation or answer-quality claim',
    frozen_sha256=BEFORE['frozen_sha256'],annotations='../../library-runs/20260927-v2-pdf-live/anchor-labels.json',
    changes=['Selected-rank immediate child fallback under parent_then_child','Same-page, same-section immediately preceding paragraph added to table context'],
    limitations=['Candidate retrieval, reranking, corpus and questions fixed; no retrieval gain is claimed.',
        'Literal Yaoliang Yu anchor does not match joined parser text; four Alabama values remain absent.',
        'The source-bound assessor quote failure remains outside this change.',
        'Preceding text is structural adjacency, not a certified semantic unit association.',
        'A parent that fits can still consume budget needed by a later requirement; this is not a child-first reservation policy.'],
    rows=rows,metric_inventory=inventory)
path=ROOT/'comparison-2.json';assert not path.exists();path.write_text(json.dumps(result,indent=2)+'\n')
print('Context anchor coverage:',coverage)
print('Improved pairs:',[(r['case_id'],r['arm'],r['improved']) for r in rows if r['improved']])
print('Regressed pairs:',[(r['case_id'],r['arm'],r['regressed']) for r in rows if r['regressed']])
