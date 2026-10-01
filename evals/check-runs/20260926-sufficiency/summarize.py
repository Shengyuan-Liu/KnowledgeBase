"""Derive the complete metric inventory from the retained offline replays."""
import importlib.metadata
import json
import math
from pathlib import Path
import platform
from statistics import mean

root = Path(__file__).parent
path = root / 'measurement-supplement.json'
assert not path.exists(), 'Append-only: choose a new report name.'
replays = {}
for name in ['comparison-1', 'comparison-2']:
    report = json.loads((root / f'{name}-details.json').read_text())
    inventory = json.loads((root / f'{name}.json').read_text())['metric_inventory']
    def metric(key, status, value, unit, n, method, reason):
        inventory[key] = dict(status=status, value=value, unit=unit, sample_count=n,
            population='Frozen offline fixture', method=method, reason=reason,
            aggregation='Macro mean per variant unless specified', artifact=f'{name}-details.json')
    for key in report['aggregates']['before']:
        metric(key, 'measured', {v: report['aggregates'][v][key] for v in ['before', 'after']},
            'fraction', 5, report['protocol'], 'Mechanical controller ablation, not live model quality.')
    def distribution(values):
        return dict(count=len(values), mean=mean(values), p50=sorted(values)[math.ceil(len(values)*.5)-1],
                    p95=sorted(values)[math.ceil(len(values)*.95)-1])
    times = {}
    for v in ['before', 'after']:
        times[v] = {'service_including_save': distribution([r[v]['service_seconds'] for r in report['cases']]),
                    'retrieval_including_source_lookup': distribution([r[v]['answer']['retrieval']['retrieval_seconds'] for r in report['cases']])}
        times[v]['planning'] = distribution([r[v]['answer']['retrieval']['planning']['planner']['seconds'] for r in report['cases']])
        assessments = [a['record']['seconds'] for r in report['cases']
                       for a in r[v]['answer']['retrieval']['planning'].get('hops', {}).get('assessments', []) if a['record']]
        times[v]['assessment'] = distribution(assessments) if assessments else {'status': 'not_applicable', 'reason': 'Disabled in before control.'}
    metric('Stage latency', 'measured', times, 'seconds', 6,
        'perf_counter; mean and nearest-rank P50/P95. Each variant six sequential service calls, including storage. Assessment count excludes deterministic empty-context decisions.',
        'Local mock diagnostics. No model loading or provider queue; cold tokenizer possible, control first. Per-query/packing timings retained in traces; no production performance claim.')
    metric('Complete-response latency', 'measured', {v: times[v]['service_including_save'] for v in times}, 'seconds', 6,
        'Synchronous answer_in_conversation entry to completed exchange after save; no HTTP transport.',
        'Complete local service latency only; model responses are test doubles.')
    metric('First-answer-delta latency', 'not_applicable', None, None, None,
        'Not exercised', 'Synchronous comparison; no streaming deltas. Browser durations are not first-delta latency.')
    metric('Reliability', 'measured', dict(completed=12, errors=0, timeouts=0, retries=0, success_rate=1), 'count and fraction', 12,
        'Successful service returns and exact history assertions; counts across both variants.', 'Offline execution, not provider/network reliability. Failed test commands remain separately recorded.')
    metric('Concurrency and throughput', 'unavailable', None, None, None, 'Sequential concurrency 1',
        'No load workload or whole-workload throughput interval; this does not establish concurrency capacity.')
    metric('Token usage and cost', 'not_applicable', None, None, None, 'Mock Responses SDK',
        'No real provider tokens or billing. Local input/evidence token counts, caps and absent usage/cost are preserved in model records; live whole-turn cost remains unmeasured.')
    metric('Ingestion and index', 'not_applicable', None, None, None, 'Fixed four-span index',
        'Index creation is fixture setup; no ingestion/index performance workload. Separate contract tests exercise upload/delete/history.')
    for key in ['Answer correctness', 'Faithfulness', 'Answer completeness', 'Answer relevance', 'Citation support', 'Citation coverage', 'Abstention']:
        metric(key, 'not_applicable', None, None, None, 'No semantic judge or live answers',
            'Model answers and assessments are frozen fixtures. All-missing routing is checked as a contract; semantic appropriate/incorrect abstention is not estimated from mocks.')
    replays[name] = {'metric_inventory': inventory, 'controls': report['controls']}
path.write_text(json.dumps({'replays': replays,
    'test_count_corrections': {'backend-1': {'passed': 0, 'failed': 0, 'skipped': 0, 'collection_errors': 9,
        'reason': 'Generic runner regex matches singular error; raw pytest log explicitly reports 9 collection errors.'}},
    'environment': {'device': platform.platform(), 'python': platform.python_version(),
        'packages': {p: importlib.metadata.version(p) for p in ['openai', 'pydantic', 'anyio', 'chromadb', 'tiktoken']},
        'models': 'offline-fixture, offline-planner, offline-answer: test doubles, no model revisions', 'concurrency': 1}}, indent=2) + '\n')
print('Recorded full comparison inventories, local timing distributions and the collection-error count correction.')
