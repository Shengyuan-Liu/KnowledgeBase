"""Compute diagnostics from retained observations without any provider calls."""
from collections import Counter, defaultdict
from datetime import datetime
import json
from pathlib import Path
from statistics import mean

from labels import covered, scores

ROOT = Path(__file__).resolve().parent


def write(name, value):
    with (ROOT / name).open('x') as file:
        file.write(json.dumps(value, indent=2) + '\n')


def distribution(values):
    values = sorted(values)
    if not values:
        return None

    def percentile(fraction):
        position = (len(values) - 1) * fraction
        lower = int(position)
        return values[lower] + (values[min(lower + 1, len(values)-1)] - values[lower]) * (position-lower)

    return dict(n=len(values), mean=mean(values), p50=percentile(.5), p95=percentile(.95),
                unit='seconds', percentile_method='linear interpolation')


def analyze():
    frozen = json.loads((ROOT / 'frozen-cases.json').read_text())
    labels = json.loads((ROOT / 'frozen-labels.json').read_text())
    snapshot = json.loads((ROOT / 'index-snapshot.json').read_text())
    chunks = {c['chunk_id']: c for d in snapshot['files'] for c in d['chunks']}
    observations = [json.loads(line) for line in (ROOT / 'server-observations.jsonl').read_text().splitlines()]
    rows, timings = [], defaultdict(list)
    starts = {o['call_id']: o for o in observations if o['kind'] == 'sdk_start'}
    calls = []
    for o in observations:
        if o['kind'] not in {'sdk_complete', 'sdk_stream_terminal', 'sdk_error'}:
            continue
        start = starts[o['call_id']]
        result = o.get('result') or o.get('event', {}).get('response') or {}
        role = ('ingestion_embedding' if start['request'] == 'ingest-apple' else 'query_embedding') if start['api'] == 'embeddings' else (
            'generation' if start['input'].get('stream') else start['input'].get('text', {}).get('format', {}).get('name'))
        calls.append(dict(call_id=o['call_id'], request=o['request'], role=role, api=start['api'], seconds=o['seconds'],
                          kind=o['kind'], model=result.get('model'), usage=result.get('usage'),
                          response_status=result.get('status'), error_type=o.get('error_type')))
        timings['provider_' + role].append(o['seconds'])
    for case in frozen['cases']:
        artifact = case['id'] + '-planned.json'
        answer = json.loads((ROOT / artifact).read_text())
        diag = answer.get('answer', {}).get('retrieval', {})
        planning = diag.get('planning') or {}
        trace = planning.get('trace') or {}
        facts = case['expected_fact_ids']
        query_rows = []
        for run in trace.get('runs', []):
            d = run['result']['diagnostics']
            stage_scores = {stage: scores([m['chunk_id'] for m in d[stage]], facts, chunks, labels)
                            for stage in ['vector_matches', 'bm25_matches', 'fused_matches']}
            stage_scores['reranked'] = scores([m['chunk_id'] for m in (d.get('rerank') or {}).get('matches', [])], facts, chunks, labels)
            query_rows.append(dict(round_index=run['round_index'], query_ids=run['query_ids'], text=run['text'],
                                   seconds=run['seconds'], stage_scores=stage_scores))
            timings['retrieval_per_query'].append(run['seconds'])
            for key in ['scope_seconds', 'embedding_seconds', 'rerank_seconds']:
                if d.get(key) is not None:
                    timings['query_' + key].append(d[key])
        sources = answer.get('answer', {}).get('sources', [])
        coverage = []
        for fact in facts:
            label = labels[fact]
            supported_anchors = []
            for anchor in label['anchors']:
                supporting = [s['source_id'] for s in sources if covered([s], {'anchors': [anchor]})
                              and anchor['anchor'].casefold() in s['text'].casefold()]
                supported_anchors.append(dict(anchor=anchor['anchor'], source_ids=supporting, covered=bool(supporting)))
            coverage.append(dict(fact_id=fact, covered=all(a['covered'] for a in supported_anchors), anchors=supported_anchors))
        request_observations = [o for o in observations if o['request'] == case['id'] + '-planned']
        for o in request_observations:
            if o['kind'] == 'stage' and o['stage'] == 'planned_retrieval':
                result = o['result']
                timings['retrieval_round'].append(o['seconds'])
                timings['cross_query_merge'].append(result['trace']['merge_seconds'])
                packing = result['evidence']['diagnostics'].get('packing_seconds')
                if packing is not None:
                    timings['packing_round'].append(packing)
        rows.append(dict(case_id=case['id'], artifact=artifact, status=answer['status'],
                         first_delta=answer['first_answer_delta_seconds'], completion=answer['complete_response_seconds'],
                         at=answer['at'], selected_scores=scores(trace.get('selected_ids', []), facts, chunks, labels),
                         query_scores=query_rows, final_evidence_coverage=coverage,
                         assessment_round=planning.get('assessment', {}).get('round_index'),
                         evidence_tokens=diag.get('evidence_tokens'),
                         excluded=diag.get('excluded'), unexpanded_parents=diag.get('unexpanded_parents'),
                         history_match=all(answer.get(key) for key in ['history_matches', 'history_sources_shared_fields_match',
                                                                      'history_sources_have_only_expected_schema_extra', 'history_retrieval_matches'])))
    score_names = ['Recall@K', 'Precision@K', 'Hit Rate@K', 'MRR', 'NDCG@K', 'fact_anchor_recall']
    selected = [r['selected_scores'] for r in rows if r['selected_scores'] is not None]
    totals = defaultdict(lambda: dict(input_tokens=0, output_tokens=0, total_tokens=0, cached_input_tokens=0, calls=0))
    for call in calls:
        usage = call['usage']
        if usage is None:
            continue
        count = totals[call['role']]
        count['calls'] += 1
        count['input_tokens'] += usage.get('input_tokens', usage.get('prompt_tokens', 0))
        count['output_tokens'] += usage.get('output_tokens', 0)
        count['total_tokens'] += usage['total_tokens']
        count['cached_input_tokens'] += (usage.get('input_tokens_details') or {}).get('cached_tokens', 0)
    for role, count in totals.items():
        if role.endswith('embedding'):
            count['cached_input_tokens'] = None
            count['cached_input_status'] = 'unavailable: provider embedding usage does not expose cached counts'
            count['output_tokens'] = None
            count['output_status'] = 'not_applicable: embeddings return vectors'
    request_start = min(datetime.fromisoformat(r['at']).timestamp() for r in rows)
    request_end = max(datetime.fromisoformat(r['at']).timestamp() + r['completion'] for r in rows)
    summary = dict(
        K=5, label_scope='Frozen full-anchor binary child relevance, incomplete for equivalent/supporting passages; no-gold case excluded.',
        final_selected_macro={name: mean(r[name] for r in selected if r[name] is not None) for name in score_names},
        final_selected_case_count=len(selected),
        final_evidence_coverage=dict(covered=sum(f['covered'] for r in rows for f in r['final_evidence_coverage']),
                                     expected=sum(len(r['final_evidence_coverage']) for r in rows)),
        first_answer_delta=distribution([r['first_delta'] for r in rows if r['first_delta'] is not None]),
        complete_response=distribution([r['completion'] for r in rows if r['status'] == 'completed']),
        stages={k: distribution(v) for k, v in timings.items()},
        stage_limit='Search/BM25/fusion sub-timers and provider queue time are unavailable. Query retrieval includes embedding/search/reranking; stage timers overlap and are not additive.',
        token_usage_by_role=dict(totals), resolved_models=sorted({c['model'] for c in calls if c['model']}),
        sdk_starts=len(starts), sdk_terminals=len(calls), sdk_errors=sum(c['kind'] == 'sdk_error' for c in calls),
        sdk_timeouts=sum('Timeout' in (c['error_type'] or '') for c in calls), provider_retries=0,
        requests=Counter(r['status'] for r in rows), history_matches=sum(r['history_match'] for r in rows),
        concurrency=1, request_wall_interval_seconds=request_end-request_start,
        completed_requests_per_second=sum(r['status'] == 'completed' for r in rows)/(request_end-request_start),
        billing=dict(status='unavailable', value=None, reason='SDK reports tokens, not billed currency; no billing API used.'),
    )
    write('diagnostics.json', dict(summary=summary, cases=rows, provider_calls=calls))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    analyze()
