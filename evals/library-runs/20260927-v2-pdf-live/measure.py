"""Aggregate the retained live observations, with explicit metric populations."""
from collections import Counter, defaultdict
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import statistics

from analyze import ROOT, FROZEN, distribution, records, write
from record_check import METRICS

REVIEW = json.loads((ROOT / 'reviewed-cases.json').read_text())['rows']
RETRIEVAL = json.loads((ROOT / 'retrieval-diagnostics-v2.json').read_text())['rows']


def metric(value, unit, population, method, n, artifact, aggregation='macro mean'):
    return dict(status='measured', value=value, unit=unit, sample_count=n,
                population=population, method=method, aggregation=aggregation, artifact=artifact)


def absent(status, reason, population, artifact):
    return dict(status=status, value=None, unit=None, sample_count=None,
                population=population, method=reason, reason=reason, aggregation='none', artifact=artifact)


def mean(values):
    return statistics.mean(values) if values else None


def usage(observations):
    by_model = defaultdict(lambda: Counter(calls=0, input_tokens=0, output_tokens=0, cached_input_tokens=0))
    missing = 0
    for record in observations:
        result = record.get('result') if record['kind']=='sdk_complete' else record.get('event',{}).get('response') if record['kind']=='sdk_stream_terminal' else None
        if result is None:
            continue
        value = result.get('usage')
        if value is None:
            missing += 1
            continue
        counter = by_model[result['model']]
        counter['calls'] += 1
        counter['input_tokens'] += value.get('input_tokens', value.get('prompt_tokens', 0))
        if 'output_tokens' in value:
            counter['output_tokens'] += value['output_tokens']
        counter['cached_input_tokens'] += value.get('input_tokens_details',{}).get('cached_tokens',0)
    for model, counter in by_model.items():
        if model.startswith('text-embedding-'):
            counter['output_tokens'] = None
            counter['output_tokens_status'] = 'not_applicable'
            counter['output_tokens_reason'] = 'Embedding calls produce vectors, not generated text.'
            counter['cached_input_tokens'] = None
            counter['cached_input_tokens_status'] = 'unavailable'
            counter['cached_input_tokens_reason'] = 'Embedding usage does not expose cached input token counts.'
    return dict(by_model=dict(by_model), terminal_results_without_usage=missing,
                billed_cost=dict(status='unavailable', value=None, reason='No provider billing statement; no fabricated or estimated bill.'),
                local_compute=dict(status='measured', device='Apple Silicon; BGE reranker on MPS, parser local; details in resolved-runtime.json', cost=None,
                                   cost_status='unavailable', reason='No local energy/hardware billing measurement.'))


def stage_stats(observations):
    stages = defaultdict(list)
    calls = {r['call_id']: r for r in observations if r['kind']=='sdk_start'}
    for r in observations:
        if r['kind']=='stage':
            stages[r['stage']].append(r['seconds'])
            result = r.get('result')
            if result:
                diag = result['diagnostics'] if 'diagnostics' in result else result['evidence']['diagnostics']
                if diag.get('packing_seconds') is not None:
                    stages['packing'].append(diag['packing_seconds'])
                # A planned trace contains cumulative runs; do not sum repeated snapshots.
        if r['kind'] in ['sdk_complete','sdk_error','sdk_stream_terminal']:
            start = calls[r['call_id']]
            stage = start['api'] if start['api']=='embeddings' else start['input'].get('text',{}).get('format',{}).get('name','answer_or_rewrite')
            stages[stage].append(r['seconds'])
    return {k: distribution(v) for k,v in stages.items()}


groups = {}
for pass_name, folder in [('before', ROOT), ('repair', ROOT/'repair-1')]:
    observations = records(folder)
    run_record = json.loads((folder/'answers-run-1.json').read_text())
    for arm in ['single', 'planned']:
        reviewed = [r for r in REVIEW if r['pass_name']==pass_name and r['arm']==arm]
        retrieval = [r for r in RETRIEVAL if r['pass_name']==pass_name and r['arm']==arm and r['scores'] is not None]
        answers = [json.loads((folder/f"{c['id']}-{arm}.json").read_text()) for c in FROZEN['cases']]
        obs = [r for r in observations if r['request'] in {c['id']+'-'+arm for c in FROZEN['cases']}]
        inventory = {}
        for key in METRICS[:5]:
            inventory[key] = metric(mean([r['scores'][key] for r in retrieval]), 'ratio', '14 questions with labeled facts; missing/blocked search scores zero',
                'K=5, selected child stage; incomplete original-page literal anchor labels, binary ranking relevance. Fact-anchor Recall and child Precision are distinct units.',
                len(retrieval), 'retrieval-diagnostics-v2.json')
        for key, field in [('Final evidence coverage','supplied_evidence_coverage'), ('Answer correctness','reference_correctness'), ('Answer completeness','completeness')]:
            eligible = [r for r in reviewed if r['points']]
            value = mean([mean([p[field] for p in r['points']]) for r in eligible])
            inventory[key] = metric(value,'score 0..1','14 questions with frozen requested facts, including errors/blocked turns as zero',
                'Codex model review of original pages and actual final sources; per-question mean requested-point score; failed requests supplied no final answer evidence.',
                len(eligible),'reviewed-cases.json')
            inventory[key]['point_micro_average'] = mean([p[field] for r in eligible for p in r['points']])
            inventory[key]['point_count'] = sum(len(r['points']) for r in eligible)
        claims = [c for r in reviewed for c in r['factual_claim_groups']]
        for key, field in [('Faithfulness','context_support'),('Citation support','citation_support'),('Citation coverage','citation_coverage')]:
            values = [c[field] for c in claims if c[field] is not None]
            inventory[key] = metric(mean(values),'score 0..1','Completed answers with factual claim groups; claim-free refusals and errors excluded',
                'Source inspection, 0/0.5/1 support per factual paragraph/bullet; pooled cited passages per claim group. Missing-point handling is separate.',
                len(values),'reviewed-cases.json','micro mean over reviewed claim groups')
        inventory['Answer relevance'] = metric(mean([r['relevance'] for r in reviewed]),'score 0..1','All 16 intended turns',
            '1 for a response addressing the requested topic including a relevant refusal; 0 for errors/blocked turns or wrong-document clarification.',16,'reviewed-cases.json')
        inventory['Abstention'] = metric(dict(
            appropriate=dict(numerator=sum(r['appropriate_abstention'] for r in reviewed), denominator=2),
            incorrect=dict(numerator=sum(r['incorrect_abstention'] for r in reviewed), denominator=14),
            missing_points_correct=dict(numerator=sum(p['correctly_stated'] for r in reviewed for p in r['missing_point_review']),denominator=4)),
            'counts and rates','Two fully unanswerable / 14 answerable questions; two partial and two fully missing points',
            'Full refusal only; errors are unsuccessful requests, not abstentions. Partial withholding does not count as a full refusal.',16,'reviewed-cases.json','separate denominators')
        for key, field in [('First-answer-delta latency','first_answer_delta_seconds'), ('Complete-response latency','complete_response_seconds')]:
            values = [a[field] for a in answers if a['status']=='completed' and a.get(field) is not None]
            inventory[key] = metric(distribution(values),'seconds','Successful SSE requests including deterministic replies',
                'Client perf_counter: HTTP request start to first nonempty final-answer delta / stream close; server startup excluded, per-request queue/provider waits included.',
                len(values), 'individual case-arm JSON files','mean/P50/P95; linear percentiles')
        inventory['Stage latency'] = metric(stage_stats(obs),'seconds','Observed calls, including failed request stages',
            'SDK start to completion including network/provider waiting; retrieval wraps production entrypoint; packing diagnostic time. Repeated repacks are separate calls.',
            len(obs),'server-observations.jsonl','per-stage distributions')
        inventory['Stage latency']['unavailable'] = {'search_and_fusion_separately':'No dedicated wall-clock timer; not inferred by subtracting unlike stage boundaries.',
            'provider_queue_separately':'Provider does not expose separate queue duration.'}
        # Unique actual query runs expose reranking/embedding times independent of repacks.
        queries = {}
        for r in obs:
            if r['kind']!='stage' or 'result' not in r:
                continue
            result = r['result']
            if 'trace' in result:
                for q in result['trace']['runs']:
                    queries[(r['request'],q['text'],tuple(q['requested_file_ids'] or []))] = q['result']['diagnostics']
            else:
                queries[(r['request'],)] = result['diagnostics']
        for key in ['embedding_seconds','rerank_seconds']:
            inventory['Stage latency']['value'][key] = distribution([d[key] for d in queries.values() if d.get(key) is not None])
        inventory['Token usage and cost'] = metric(usage(obs),'provider tokens; cost unavailable','All observed terminal API responses, including failed downstream validation',
            'Actual SDK usage fields, stream response.completed usage; no character-count estimates. Embedding output tokens are not applicable.',
            sum(r['kind'] in ['sdk_complete','sdk_stream_terminal'] for r in obs),'server-observations.jsonl','sum by resolved model')
        statuses = Counter(a['status'] for a in answers)
        inventory['Reliability'] = metric(dict(intended_turns=16, submitted_requests=16-statuses['blocked'], completed=statuses['completed'],
            errors=statuses['error'], blocked=statuses['blocked'], incomplete=statuses['incomplete'], retries=0,
            timeouts=sum(r['kind']=='sdk_error' and 'Timeout' in r.get('error_type','') for r in obs),
            error_http_close_latency=distribution([a['complete_response_seconds'] for a in answers if a['status']=='error']),
            saved_answer_and_trace_parity=sum(a.get('history_matches') and a.get('history_retrieval_matches') for a in answers if a['status']=='completed')),
            'counts','All 16 intended turns, with blocked follow-up retained','SSE terminal events; completion does not establish semantic correctness.',16,'individual case-arm JSON files','counts; ratios use intended turns')
        inventory['Concurrency and throughput'] = metric(dict(concurrency=1, completed=statuses['completed'],
            paired_pass_wall_seconds=run_record['duration_seconds'],completed_per_paired_pass_second=statuses['completed']/run_record['duration_seconds']),
            'completed turns/second','Alternating arms in one sequential 32-turn workload',
            'Full paired command wall clock includes other arm, HTTP/history/client I/O; arm contributions add to overall throughput. Not a load/capacity benchmark.',16,'answers-run-1.json','pass wall-clock rate')
        inventory['Ingestion and index'] = absent('not_applicable','Answer-only comparison reuses the same isolated five-PDF index; see shared ingestion/lifecycle inventory.','answer pass','ingestion-summary.json')
        assert set(inventory)==set(METRICS)
        groups[pass_name+'-'+arm] = inventory

shared_obs = records(ROOT)
ingest_obs = [r for r in shared_obs if r['request'].startswith('ingest-')]
ingestion = json.loads((ROOT/'ingestion-summary.json').read_text())
lifecycle = json.loads((ROOT/'repair-1/lifecycle.json').read_text())
shared = {m: absent('not_applicable','Ingestion/lifecycle workload does not ask or answer questions.','five PDF uploads plus one isolated deletion','ingestion-summary.json') for m in METRICS}
shared['Stage latency'] = metric(stage_stats(ingest_obs),'seconds','Five uploads','Local parser observations include first-use model loading; SDK embeddings include provider/network waits.',5,'server-observations.jsonl','per-stage distributions')
shared['Token usage and cost'] = metric(usage(ingest_obs),'provider tokens; billed cost unavailable','Five uploaded PDFs','Actual embeddings SDK usage',5,'server-observations.jsonl','sum')
shared['Reliability'] = metric(dict(uploads=5,ready=5,original_hash_matches=5,byte_range_matches=5,errors=0,retries=0,delete_verified=True),'counts','5 uploads and 1 deletion','HTTP status, file hashes, ranged bytes and lifecycle assertions',6,'ingestion-summary.json; repair-1/lifecycle.json','counts')
shared['Ingestion and index'] = metric(dict(pdf_count=5,page_count=98,children=621,parents=154,index_bytes_after_ingestion=ingestion['index_bytes'],
    upload_to_ready=distribution([r['seconds'] for r in ingestion['results']]),delete_and_history_verification_seconds=lifecycle['seconds'],
    index_bytes_after_delete=lifecycle['index_bytes_after'],original_after_delete_status=lifecycle['original_status'],
    history_preserved=lifecycle['history_retrieval_matches'],update=lifecycle['update_behavior']),
    'seconds, bytes and counts','The same five byte-identical PDFs; delete only apple-fy24.pdf from the disposable index',
    'POST start through synchronous Ready response; total bytes of all data-dir files (including originals/SQLite/vector index). After-delete bytes also contain 56 saved answer histories and must not be interpreted as storage reclaimed.',6,'ingestion-summary.json; index-snapshot.json; repair-1/lifecycle.json','per-upload distributions and absolute sizes')
shared['Concurrency and throughput'] = metric(dict(concurrency=1,files=5,total_upload_seconds=sum(r['seconds'] for r in ingestion['results']),
    files_per_upload_second=5/sum(r['seconds'] for r in ingestion['results'])), 'files/second','Five sequential upload calls','Excludes between-call hash/range verification; includes first-use parser load.',5,'ingestion-summary.json','upload service-time rate')

write('measurement-v2.json', dict(scope='Development acceptance failed; no release or merge approval', reviewer='Codex model; no independent human review',
    corrections={'embedding_usage_fields':'Supersedes measurement.json: embedding output tokens are not_applicable and cached input tokens unavailable, not zero. All measured values and quality scores unchanged.',
                 'live_wrapper_inventory':'Overrides incorrect offline-only metric statuses in ingest-run-1, answers-run-1 and repair-1/answers-run-1 and lifecycle-run-1; raw records preserved.',
                 'retrieval_diagnostics':'retrieval-diagnostics-v2.json supersedes v1 per-query reranked values: v1 mistakenly read the prerank candidates rather than sorted matches. Final-selected metrics are unchanged.',
                 'source_review_preparation':'Source extraction/rendering and freeze preparation commands predated the generic command wrapper. Original pages, extracted text and fixture hashes retained; exact preparation command duration unavailable. No paid call or performance claim attached.'},
    validity={'development_only':True,'no_independent_human_review':True,'same_index_and_corpus':True,'no_retry':True,
              'paid_replay_count':1,'backend_test_contention':'backend-tests-1 (26.74s pytest duration) overlapped early repair-pass requests. Latency changes cannot be attributed solely to product changes; no extra paid pass was run for cleaner timing.',
              'missing_acceptance_populations':['genuine contradictory evidence','independent held-out corpus','load/concurrency above one','printed-page-label matching','billing statement'],
              'scope':'OCR/visual/formula capabilities are deferred. No live browser was run this turn; original bytes/ranges/page counts/history/delete were verified via HTTP. Prior browser coverage is not represented as current browser evidence.'},
    fixture_sha256=sha256((ROOT/'effective-cases.json').read_bytes()).hexdigest(),
    runtime_artifacts=['resolved-runtime.json','repair-1/resolved-runtime.json'],groups=groups,shared_ingestion_lifecycle=shared))
for name, metrics in groups.items():
    print(name, 'correctness',round(metrics['Answer correctness']['value'],4),'evidence',round(metrics['Final evidence coverage']['value'],4),
          'faithfulness',round(metrics['Faithfulness']['value'],4),'citation support',round(metrics['Citation support']['value'],4),
          'citation coverage',round(metrics['Citation coverage']['value'],4),'success',metrics['Reliability']['value']['completed'],
          'latency',metrics['Complete-response latency']['value'])
