"""Publish the full metric inventory with explicit measurement boundaries."""
from datetime import datetime, timezone
import json
from pathlib import Path

from record_check import METRICS

ROOT = Path(__file__).resolve().parent


def main():
    diagnostics = json.loads((ROOT / 'diagnostics.json').read_text())
    d = diagnostics['summary']
    review = json.loads((ROOT / 'review.json').read_text())['summary']
    ingest = json.loads((ROOT / 'ingest-apple.json').read_text())
    runtime = json.loads((ROOT / 'resolved-runtime.json').read_text())
    stop = json.loads((ROOT / 'server-stop.json').read_text())
    snapshot = json.loads((ROOT / 'index-snapshot.json').read_text())
    inventory = {}

    def measured(name, value, unit, count, population, method, artifact, aggregation):
        inventory[name] = dict(status='measured', value=value, unit=unit, sample_count=count, population=population,
                               method=method, artifact=artifact, aggregation=aggregation)

    for name in METRICS[:5]:
        measured(name, d['final_selected_macro'][name], 'ratio', 5, 'Five answerable cases, final-round selected children',
                 'K=5; complete-anchor binary child labels within frozen physical pages. Enumerated allowed-file children; non-exhaustive semantic relevance. Full formulas in protocol.md. Per-query vector/BM25/fusion/rerank observations retained separately.',
                 'diagnostics.json', 'Unweighted case macro mean')
    for name, key in [('Final evidence coverage', 'final_evidence_coverage')]:
        measured(name, d[key], 'facts', 16, 'Sixteen expected source-fact anchor groups',
                 'Every anchor must occur in supplied source text and its preserved source range. Distinct from semantic support review.',
                 'diagnostics.json', '14/16 micro coverage; per-case records retained')
    for name, key, count in [('Answer correctness', 'correctness', 16), ('Faithfulness', 'faithfulness', 15),
                              ('Answer completeness', 'completeness', 16), ('Answer relevance', 'relevance', 6),
                              ('Citation support', 'citation_support', 15), ('Citation coverage', 'citation_coverage', 15)]:
        measured(name, review[key], 'review units', count, 'Frozen expected points or emitted atomic factual claims as named in value',
                 'Codex model review, not human ground truth; all outputs inspected against original pages and supplied context. Claim-free refusal has no citation denominator.',
                 'review.json', 'Micro numerator/denominator; binary relevance per case')
    measured('Abstention', review['abstention'], 'requests', 6, 'One unanswerable and five answerable cases',
             'Separate appropriate refusal, incorrect partial/any refusal and incorrect full refusal.', 'review.json', 'Separate denominators; 1/1 appropriate, 1/5 incorrect partial, 0/5 incorrect full')
    for name, key in [('First-answer-delta latency', 'first_answer_delta'), ('Complete-response latency', 'complete_response')]:
        measured(name, d[key], 'seconds', 6, 'Six completed sequential HTTP/SSE requests, including the local refusal',
                 'Client request start to first nonempty answer_delta / end of HTTP stream respectively; metadata excluded. Network/queue time included, server startup excluded.',
                 'diagnostics.json', 'Mean/P50/P95; linear interpolation; no warmup requests')
    measured('Stage latency', dict(distributions=d['stages'], startup_seconds=runtime['startup_seconds'],
                                   unavailable=dict(search_fusion='Vector search, BM25 and fusion have no separate timers.', provider_queue='Provider queue wait is included but not separately exposed.')),
             'seconds', None, '22 unique query runs; 14 retrieve/repack invocations; 6 plans; 10 assessments; 5 answer generations',
             'Observed SDK and product timings. Retrieve/repack invocations include rounds without new queries. Overlapping timings are not additive.',
             'diagnostics.json; resolved-runtime.json', 'Count/mean/P50/P95 by stage, startup separate')
    usage = json.loads(json.dumps(d['token_usage_by_role']))
    for role in ['query_embedding', 'ingestion_embedding']:
        usage[role]['cached_input_tokens'] = None
        usage[role]['cached_input_status'] = 'unavailable: embedding usage does not expose cached-token counts'
        usage[role]['output_tokens'] = None
        usage[role]['output_status'] = 'not_applicable: embedding calls return vectors, not completion tokens'
    measured('Token usage and cost', dict(by_role=usage, resolved_models=d['resolved_models'],
                                          evidence_tokens={r['case_id']: r['evidence_tokens'] for r in diagnostics['cases']},
                                          billed_cost=d['billing'], local_compute={'parser': 'cpu', 'retrieval': 'local CPU', 'reranker': runtime['reranker'], 'billing': 'No provider currency inferred for local compute.'}),
             'tokens; currency unavailable', 44, 'All 44 provider calls including one ingestion embedding batch',
             'Actual SDK usage. Corrected interpretation: diagnostics.json initializes cached counters to zero; for embedding calls those absent counters are unavailable, not measured zero. This inventory supersedes those two cached/output placeholder fields without changing raw observations.',
             'server-observations.jsonl; diagnostics.json; resolved-runtime.json', 'Sum by role, preserving embedding versus response usage')
    measured('Reliability', dict(http_requests=6, completed=6, errors=0, timeouts=0, retries=0,
                                sdk_calls=d['sdk_starts'], sdk_terminals=d['sdk_terminals'], sdk_errors=d['sdk_errors'],
                                sdk_timeouts=d['sdk_timeouts'], sdk_retries=d['provider_retries'], semantic_gate=review['case_gate']),
             'counts and rates', 6, 'Six user requests; provider attempts reported separately',
             'HTTP/SSE outcomes and observed SDK starts/terminals. Successful transport is separate from the 5/6 semantic gate.',
             'diagnostics.json; review.json', 'Completion 6/6; SDK success 44/44; semantic acceptance 5/6')
    measured('Concurrency and throughput', dict(concurrency=1, wall_interval_seconds=d['request_wall_interval_seconds'],
                                               completed_requests_per_second=d['completed_requests_per_second']),
             'requests/second', 6, 'From first answer-request start to final HTTP completion, including intervening history reads',
             'Six sequential planned requests; not a load/capacity benchmark.', 'diagnostics.json', 'Completed requests / observed wall interval')
    measured('Ingestion and index', dict(ingested_file='apple-fy24.pdf', pages=4,
                                        upload_to_ready_seconds=ingest['seconds'],
                                        storage_bytes_before=ingest['index_bytes_before'], storage_bytes_after_ingestion=snapshot['index_bytes'],
                                        storage_bytes_after_answers=stop['index_bytes_after_answers'],
                                        ready_corpus_files=len(snapshot['files']), ready_corpus_pages=sum(len(d['extraction']['pages']) for d in snapshot['files']),
                                        queried_files=3, queried_pages=88, originals_verified=3,
                                        update=dict(status='not_applicable', reason='No update operation in this workload.'),
                                        delete=dict(status='not_applicable', reason='No deletion operation in this workload.'),
                                        reindex='Only Apple was newly indexed; paper/lecture extraction and embeddings were reused.'),
             'seconds; bytes; counts', 1, 'One Apple upload plus an existing four-file evaluation index',
             'Client POST duration to ready; storage totals include original PDFs, vectors, SQLite metadata and historical/new conversations. Not vector-only size. Original bytes/ranges/revision guard checked for three queried PDFs.',
             'ingest-apple.json; original-access.json; index-snapshot.json; server-stop.json', 'Single upload: mean/P50/P95 all equal its observed duration; no capacity inference')
    assert set(inventory) == set(METRICS)
    record = dict(at=datetime.now(timezone.utc).isoformat(), code_commit=runtime['code_commit'],
                  implementation_commit='5541597', metric_inventory=inventory,
                  limitations=['New questions on a reused development corpus; no before/after comparison.',
                               'One incorrect partial refusal; incomplete retrieval labels; no human reviewer.',
                               'No dependent entity hop, browser interaction, OCR, chart or formula evaluation.',
                               'Billed cost and isolated search/fusion/provider queue timings unavailable.',
                               'Mixed ingestion vintages; all indexed extraction and parser provenance retained.'])
    with (ROOT / 'measurement-v2.json').open('x') as file:
        file.write(json.dumps(record, indent=2) + '\n')
    print('Recorded all 20 metrics, the lecture failure, and unavailable cost/timing fields.')


if __name__ == '__main__':
    main()
