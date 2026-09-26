"""Record the frozen final v1 real-provider browser workflow."""
import json
import os
from pathlib import Path
import platform
import re
import subprocess
from time import perf_counter, time

from evals import metrics
from evals.evaluate import digest, git_state, timestamp, write_json
from knowledgebase.config import Settings

root = Path.cwd()
directory = Path(__file__).parent
run_id = directory.name
data_dir = root / 'data/live-browser' / run_id
if (directory / 'run.json').exists() or data_dir.exists():
    raise SystemExit('Historical attempts are append-only; use a new run directory.')
command = ['npx', 'playwright', 'test', '--config', 'playwright.release.config.ts']
overrides = {'LIVE_RUN_ID': run_id, 'DATA_DIR': str(data_dir),
    'CHUNKING_STRATEGY': 'parent_child', 'CHUNK_MAX_TOKENS': '512', 'PARENT_MAX_TOKENS': '1536',
    'CHUNK_TOKENIZER': 'cl100k_base', 'EVIDENCE_MAX_TOKENS': '4096',
    'EVIDENCE_PACKING_STRATEGY': 'parent_then_child', 'RETRIEVAL_STRATEGY': 'hybrid',
    'RETRIEVAL_TOP_K': '5', 'RETRIEVAL_CANDIDATE_LIMIT': '20', 'RRF_K': '60',
    'BM25_K1': '1.2', 'BM25_B': '0.75', 'RERANK_ENABLED': 'false', 'RERANK_UNIT': 'child',
    'ANSWER_MODEL': 'gpt-4.1', 'EMBEDDING_MODEL': 'text-embedding-3-small',
    'OPENAI_MAX_RETRIES': '0', 'OPENAI_TIMEOUT_SECONDS': '60'}
env = {**os.environ, **overrides}
os.environ.update(overrides)
settings = Settings()
if settings.answer_reasoning_effort is not None or settings.resolver_model not in (None, 'gpt-4.1'):
    raise SystemExit('Frozen reasoning/resolver configuration differs from local settings.')
state = git_state()
state['browser_code_sha256'] = {str(p): digest(p.read_bytes()) for p in [
    Path('frontend/live/release.spec.ts'), Path('frontend/playwright.release.config.ts'),
    Path('frontend/playwright.live.config.ts'), directory / 'PLAN.md', Path(__file__)]}
state['frontend_sha256'] = {str(p): digest(p.read_bytes()) for p in sorted(Path('frontend/src').rglob('*')) if p.is_file()}
report = {'started_at': timestamp(), 'command': command, 'cwd': 'frontend', 'environment_overrides': overrides,
    'git': state, 'settings': settings.model_dump(mode='json', exclude={'openai_api_key', 'openai_base_url'}),
    'device': platform.platform(), 'concurrency': 1, 'retries': 0,
    'warmup': 'Fresh isolated index and server; existing build; no separate warmup.',
    'power_assertions': subprocess.run(['pmset', '-g', 'assertions'], capture_output=True, text=True).stdout,
    'status': 'running', 'scope': 'PLAN.md; three completed real-provider questions, one cancellation, TXT/Markdown ingestion, history and deletion.'}
write_json(directory / 'run.json', report)
started, wall = perf_counter(), time()
result = subprocess.run(command, cwd='frontend', env=env, capture_output=True, text=True)
elapsed, wall_elapsed = perf_counter() - started, time() - wall
output = result.stdout + result.stderr
(directory / 'browser.log').write_text(output)
report.update(finished_at=timestamp(), duration_seconds=elapsed, wall_seconds=wall_elapsed,
    exit_code=result.returncode, counts={s: int(n) for n, s in re.findall(r'(\d+) (passed|failed|skipped)', output)},
    status='passed' if result.returncode == 0 else 'failed')
template = json.loads(Path('evals/library-runs/20260926-comparison-awake/metrics.json').read_text())['metrics']
inventory = {name: metrics.missing('This bounded browser workflow does not instrument or annotate this metric; exact answers and diagnostics are retained for separate review.') for name in template}
for name in ('judge_reliability', 'judge_seconds', 'appropriate_abstention'):
    inventory[name] = metrics.missing('No judge or unanswerable case in this workflow.', False)
for name in ('first_delta_seconds', 'generation_seconds', 'generation_first_delta_seconds', 'total_seconds'):
    inventory[name] = metrics.missing('UI completion includes browser polling; exact transport/generation start and first delta are not instrumented.')
for name in ('cost', 'token_usage'):
    inventory[name] = metrics.missing('Unmodified production API does not expose actual upstream usage or billed cost; not inferred from call upper bounds.')
inventory['search_fusion_seconds'] = metrics.missing('No independent search/fusion timer.')
inventory['model_loading'] = metrics.missing('Startup not separately timed; reranking disabled, no local reranker loaded.', False)
inventory['concurrency_throughput'] = metrics.missing('One sequential workflow includes UI inspection and lifecycle actions; not a throughput workload.')
inventory['reliability'] = metrics.measured({'exit_code': result.returncode, 'counts': report['counts'], 'test_retries': 0, 'sdk_retries': 0}, 'browser workflows', 1, 'One frozen attempt; see browser.log for failures. Upstream actual request counts unavailable.', 'browser.log')
if (directory / 'acceptance.json').exists():
    acceptance = json.loads((directory / 'acceptance.json').read_text())
    answers = acceptance['answers']
    inventory['ui_complete_seconds'] = metrics.timing([a['ui_complete_ms'] / 1000 for a in answers])
    inventory['ui_complete_seconds'].update(artifact='acceptance.json', scope='Composer fill/submit to visible Completed; browser polling included, server startup excluded. Not HTTP completion.')
    for name in ('retrieval_seconds', 'embedding_seconds', 'rerank_seconds', 'packing_seconds'):
        inventory[name] = metrics.timing([a['saved']['messages'][-1]['retrieval'].get(name) for a in answers])
        inventory[name]['artifact'] = 'acceptance.json'
    inventory['evidence_tokens'] = metrics.measured([a['saved']['messages'][-1]['retrieval']['evidence_tokens'] for a in answers], 'tokens', len(answers), 'Actual supplied evidence including labels.', 'acceptance.json')
    inventory['ingestion'] = metrics.timing([s['details']['elapsed_ms'] / 1000 for s in acceptance['steps'] if s['name'] == 'upload-ready'])
    inventory['ingestion'].update(artifact='acceptance.json', scope='File input to visible Ready, two synthetic files; includes browser polling.')
    inventory['update_delete'] = metrics.measured({'deletion_verified': any(s['name'] == 'deletion-and-historical-evidence' for s in acceptance['steps']), 'update': 'not_applicable; no update endpoint'}, 'checks', 1, 'Live SQLite tables and file list empty; historical snapshots retained.', 'acceptance.json')
    stored = directory / 'storage-before-deletion.json'
    if stored.exists():
        inventory['index_bytes'] = metrics.measured(json.loads(stored.read_text())['index_bytes'], 'bytes', 1, 'All files under isolated DATA_DIR after ingestion, including SQLite/WAL and vector index overhead; not marginal content size.', stored.name)
report['metric_inventory'] = inventory
write_json(directory / 'run.json', report)
print(output)
raise SystemExit(result.returncode)
