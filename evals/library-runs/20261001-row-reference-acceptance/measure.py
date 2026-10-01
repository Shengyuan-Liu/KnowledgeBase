"""Record the complete live metric inventory and matched per-case comparison."""
from datetime import datetime, timezone
import json
from pathlib import Path
from record_check import METRICS

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT.parent / '20260929-pdf-heading-acceptance'


def read(name, root=ROOT):
    return json.loads((root/name).read_text())


def main():
    diagnostics, review = read('diagnostics.json'), read('review.json')
    d, r = diagnostics['summary'], review['summary']
    runtime, stop, snapshot, reuse = [read(n) for n in ['resolved-runtime.json','server-stop.json','index-snapshot.json','index-reuse.json']]
    inventory = {}
    def measured(name, value, unit, count, population, method, artifact, aggregation):
        inventory[name] = dict(status='measured', value=value, unit=unit, sample_count=count,
            population=population, method=method, artifact=artifact, aggregation=aggregation)
    for name in METRICS[:5]:
        measured(name, d['final_selected_macro'][name], 'ratio', 5, 'Five answerable cases; final-round selected children',
            'K=5; frozen full-anchor binary child labels, all allowed-file children enumerated. Non-exhaustive semantic relevance. Same child contents/IDs and labels as baseline. Per-query vector/BM25/fusion/rerank scores retained separately.',
            'diagnostics.json', 'Unweighted case macro mean; no-gold case excluded')
    measured('Final evidence coverage', d['final_evidence_coverage'], 'source-fact groups', 16, 'Frozen expected source anchors',
        'All anchors occur in actual supplied source text/ranges. Separate from semantic answer review.', 'diagnostics.json', 'Micro covered/expected; per-case values retained')
    for name, key, denominator in [('Answer correctness','correctness','expected'),('Answer completeness','completeness','expected'),
        ('Faithfulness','faithfulness','claims'),('Answer relevance','relevance','total'),
        ('Citation support','citation_support','cited_claims'),('Citation coverage','citation_coverage','citation_required_claims')]:
        measured(name, r[key], 'review units', r[key][denominator], 'Expected facts or emitted factual claims as named in value',
            'Codex model review using unchanged rubric, not human ground truth. Every point/claim compared to exact context and original pages. Claim-free refusal has no citation denominator.',
            'review.json', 'Micro counts; binary relevance per response')
    measured('Abstention', r['abstention'], 'requests', 6, 'One unanswerable and five answerable questions',
        'Appropriate refusal and incorrect partial/full refusal have separate denominators.', 'review.json', 'Separate numerator/denominator counts')
    for name,key in [('First-answer-delta latency','first_answer_delta'),('Complete-response latency','complete_response')]:
        measured(name,d[key],'seconds',d[key]['n'],'Sequential HTTP/SSE requests, including local refusal',
            'Client start to first nonempty answer delta / HTTP stream end. Network/queue included; startup excluded; no warmup.',
            'diagnostics.json','Count/mean/P50/P95, linear interpolation')
    measured('Stage latency',dict(distributions=d['stages'],startup_seconds=runtime['startup_seconds'],
        unavailable={'search_fusion':'No separate vector/BM25/fusion timers.','provider_queue':'Included in provider timing but not separately exposed.'}),
        'seconds',None,'Observed SDK calls and production retrieval/repacking stages',
        'perf_counter observers and product timers. Retrieval rounds may repack without new queries; overlapping timers are not additive. Reranker on recorded MPS device, other local retrieval on CPU.',
        'diagnostics.json; resolved-runtime.json','Count/mean/P50/P95 by stage; startup separate')
    measured('Token usage and cost',dict(by_role=d['token_usage_by_role'],resolved_models=d['resolved_models'],
        evidence_tokens={row['case_id']:row['evidence_tokens'] for row in diagnostics['cases']},
        billed_cost=d['billing'],local_compute={'retrieval':'CPU','reranker':runtime['reranker'],'parsing':'not exercised'}),
        'tokens; currency unavailable',d['sdk_starts'],'All provider calls in six answer requests; no ingestion or paid judge',
        'Actual SDK usage; missing embedding cache counts unavailable, embedding output counts not applicable. Local compute is separate from provider usage.',
        'server-observations.jsonl; diagnostics.json; resolved-runtime.json','Sum by role; evidence context tokens per case')
    requests=d['requests']
    measured('Reliability',dict(http_requests=sum(requests.values()),outcomes=requests,
        sdk_calls=d['sdk_starts'],sdk_terminals=d['sdk_terminals'],sdk_errors=d['sdk_errors'],sdk_timeouts=d['sdk_timeouts'],
        retries=d['provider_retries'],semantic_gate=r['case_gate']), 'counts and rates',6,'User requests and SDK attempts separately',
        'Transport completion is separate from semantic acceptance. Preserve all failures; no retries.',
        'diagnostics.json; review.json','Counts with explicit denominators')
    measured('Concurrency and throughput',dict(concurrency=1,wall_interval_seconds=d['request_wall_interval_seconds'],
        completed_requests_per_second=d['completed_requests_per_second']),'requests/second',6,'First answer request through final HTTP completion',
        'Includes intervening history reads; sequential workload is not a load/capacity test.','diagnostics.json','Completed requests / measured wall interval')
    measured('Ingestion and index',dict(
        storage_bytes_before=sum(v['bytes'] for v in reuse['source_file_hashes'].values()),
        storage_bytes_at_start=snapshot['index_bytes'],storage_bytes_after_answers=stop['index_bytes_after_answers'],
        ready_corpus_files=len(snapshot['files']),ready_corpus_pages=sum(len(x['extraction']['pages']) for x in snapshot['files']),
        queried_files=3,queried_pages=88,
        upload={'status':'not_applicable','value':None,'reason':'Byte-identical frozen index copy; no upload, parsing or document embedding.'},
        rebuild={'status':'not_applicable','value':None,'reason':'Parents and child links copied unchanged.'},
        delete={'status':'not_applicable','value':None,'reason':'No deletion operation.'},
        public_update={'status':'not_applicable','value':None,'reason':'No public update operation.'},
        original_access=read('original-access.json'),baseline_unchanged=stop['baseline_directory_unchanged']),
        'bytes; counts',5,'Five-PDF isolated index; three queried originals',
        'Total storage includes PDFs, vectors, metadata and historical/new answers; not vector-only size or ingestion latency. Indexed tables and baseline are unchanged.',
        'index-reuse.json; original-access.json; server-stop.json','Storage counts; no ingestion duration')
    assert set(inventory)==set(METRICS)
    old_d, old_r = read('diagnostics.json',BASELINE),read('review.json',BASELINE)
    pairs=[]
    for case,diag in zip(review['cases'],diagnostics['cases'],strict=True):
        before=next(c for c in old_r['cases'] if c['case_id']==case['case_id'])
        bd=next(c for c in old_d['cases'] if c['case_id']==case['case_id'])
        before_points={p['fact_id']:p for p in before['expected_points']}
        pairs.append(dict(case_id=case['case_id'],before_passed=before['passed'],after_passed=case['passed'],
            improved_points=[p['fact_id'] for p in case['expected_points'] if p['correct'] and not before_points[p['fact_id']]['correct']],
            regressed_points=[p['fact_id'] for p in case['expected_points'] if not p['correct'] and before_points[p['fact_id']]['correct']],
            before_evidence=bd['final_evidence_coverage'],after_evidence=diag['final_evidence_coverage'],
            before_first_delta=bd['first_delta'],after_first_delta=diag['first_delta'],
            before_completion=bd['completion'],after_completion=diag['completion'],
            before_assessment_round=bd['assessment_round'],after_assessment_round=diag['assessment_round'],
            before_evidence_tokens=bd['evidence_tokens'],after_evidence_tokens=diag['evidence_tokens']))
    comparison=dict(before_review=old_r['summary'],after_review=r,pairs=pairs,
        before_retrieval=old_d['summary']['final_selected_macro'],after_retrieval=d['final_selected_macro'],
        before_latency={k:old_d['summary'][k] for k in ['first_answer_delta','complete_response','stages']},
        after_latency={k:d[k] for k in ['first_answer_delta','complete_response','stages']},
        before_answer_only_usage={k:v for k,v in read('measurement.json',BASELINE)['metric_inventory']['Token usage and cost']['value']['by_role'].items() if k!='ingestion_embedding'},
        after_answer_only_usage=d['token_usage_by_role'])
    record=dict(at=datetime.now(timezone.utc).isoformat(),code_commit=runtime['code_commit'],metric_inventory=inventory,
        comparison=comparison,limitations=['Same familiar development corpus/questions; Codex model review, no independent human or held-out benchmark.',
            'One live sample per case per arm. Stochastic planning, cached provider tokens and network timings limit causal speed/quality claims.',
            'Frozen index copied without reindexing; no live ingestion/update/delete regression claim.',
            'Incomplete retrieval labels; no unknown-entity dependent-hop, browser, OCR, chart or formula acceptance.',
            'Provider billed cost and isolated search/fusion/queue times unavailable.'])
    with (ROOT/'measurement.json').open('x') as file:
        file.write(json.dumps(record,indent=2)+'\n')
    print('Recorded all 20 policy metrics and six matched before/after cases; both arms contain answer calls only.')


if __name__=='__main__':
    main()
