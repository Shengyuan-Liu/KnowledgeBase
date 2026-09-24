"""Measure real HTTP first-delta and full completion times on an isolated library copy."""

import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
from tempfile import TemporaryDirectory
import time

import httpx

from evals.evaluate import retrieval_metrics
from knowledgebase.config import Settings


def timing(values):
    ordered = sorted(values)
    return {'n': len(values), 'mean': statistics.mean(values),
            'p50': ordered[math.ceil(len(values) * 0.50) - 1],
            'p95': ordered[math.ceil(len(values) * 0.95) - 1]}


def run():
    report = Path(__file__).parent
    cases = json.loads((report / 'cases.json').read_text())
    settings = Settings()
    assert settings.rerank_enabled and settings.rerank_model == 'BAAI/bge-reranker-v2-m3'
    rows = []
    with TemporaryDirectory(prefix='knowledgebase-packing-eval-') as temporary:
        library = Path(temporary) / 'library'
        library.mkdir()
        # Stop the source API before this copy so SQLite and Chroma are quiescent.
        shutil.copy2(settings.data_dir / 'knowledgebase.db', library / 'knowledgebase.db')
        shutil.copytree(settings.data_dir / 'chroma', library / 'chroma')
        env = {**os.environ, 'DATA_DIR': str(library), 'PYTHONPATH': str(Path.cwd()),
               'OPENAI_TIMEOUT_SECONDS': '90', 'OPENAI_MAX_RETRIES': '1'}
        with (report / 'server.log').open('x') as log:
            started = time.perf_counter()
            server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'stream_server:app',
                                       '--app-dir', str(report), '--host', '127.0.0.1', '--port', '8002'],
                                      env=env, stdout=log, stderr=log)
            try:
                with httpx.Client(base_url='http://127.0.0.1:8002', timeout=120) as client:
                    while True:
                        if server.poll() is not None:
                            raise RuntimeError('Evaluation server exited; inspect server.log')
                        try:
                            response = client.get('/benchmark/info', timeout=1)
                            if response.status_code == 200:
                                break
                        except httpx.TransportError:
                            pass
                        if time.perf_counter() - started > 60:
                            raise TimeoutError('Evaluation server did not start')
                        time.sleep(0.2)
                    startup = time.perf_counter() - started
                    info = response.json()
                    assert info['snapshot'] == json.loads((report / 'chunks.json').read_text())
                    with (report / 'run.json').open('x') as output:
                        json.dump({**{k: v for k, v in info.items() if k != 'snapshot'},
                                   'base_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                                   'working_diff_sha256': hashlib.sha256(subprocess.check_output(['git', 'diff'])).hexdigest(),
                                   'cases_sha256': hashlib.sha256((report / 'cases.json').read_bytes()).hexdigest(),
                                   'concurrency': 1, 'startup_seconds': startup,
                                   'timeout_seconds': 90, 'max_retries': 1,
                                   'percentiles': 'nearest rank; first nonempty answer_delta for first-delta time',
                                   'warmup': 'none; cached weights loaded before requests; first query includes cold kernel effects',
                                   'provider_usage_and_billed_cost': None}, output, indent=2)
                    with (report / 'answers.jsonl').open('x') as output:
                        for index, case in enumerate(cases):
                            modes = ['parent_first', 'parent_then_child']
                            if index % 2:
                                modes.reverse()
                            for mode in modes:
                                row = {'case_id': case['id'], 'question': case['question'], 'strategy': mode,
                                       'events': [], 'first_delta_seconds': None}
                                start = time.perf_counter()
                                try:
                                    with client.stream('POST', f'/benchmark/{mode}', json={
                                        'question': case['question'], 'request_id': f"{case['id']}-{mode}",
                                    }) as response:
                                        response.raise_for_status()
                                        event = None
                                        for line in response.iter_lines():
                                            if line.startswith('event: '):
                                                event = line[7:]
                                            elif line.startswith('data: '):
                                                data = json.loads(line[6:])
                                                elapsed = time.perf_counter() - start
                                                row['events'].append({'event': event, 'seconds': elapsed, 'data': data})
                                                if event == 'answer_delta' and data['delta'] and row['first_delta_seconds'] is None:
                                                    row['first_delta_seconds'] = elapsed
                                                if event == 'complete':
                                                    row['answer'] = data
                                                    row['complete_seconds'] = elapsed
                                    row['total_seconds'] = time.perf_counter() - start
                                    assert row['events'][-1]['event'] == 'complete'
                                    answer = row['answer']
                                    normalized = {**case, 'evidence': [{**span, 'file': Path(span['file']).name} for span in case['evidence']]}
                                    row['coverage'] = retrieval_metrics(normalized, answer['sources'])
                                    saved = client.get(f"/api/conversations/{answer['conversation_id']}").json()['messages'][-1]
                                    assert saved['retrieval'] == answer['retrieval']
                                    assert saved['sources'] == [{**s, 'file_deleted': False} for s in answer['sources']]
                                    row['status'] = 'ok'
                                except Exception as error:
                                    row.update(status='error', error_type=type(error).__name__, total_seconds=time.perf_counter() - start)
                                rows.append(row)
                                output.write(json.dumps(row) + '\n')
                                output.flush()
                                print(mode, case['id'], row['status'], round(row['total_seconds'], 2), flush=True)
                    assert client.get('/benchmark/info').json()['snapshot'] == info['snapshot']
            finally:
                server.terminate()
                server.wait(timeout=30)
    summary = {}
    for mode in ['parent_first', 'parent_then_child']:
        completed = [r for r in rows if r['strategy'] == mode and r['status'] == 'ok']
        summary[mode] = {
            'completed': len(completed), 'errors': len(cases) - len(completed),
            'first_delta_seconds': timing([r['first_delta_seconds'] for r in completed]),
            'total_seconds': timing([r['total_seconds'] for r in completed]),
            'rerank_seconds': timing([r['answer']['retrieval']['rerank_seconds'] for r in completed]),
            'packing_seconds': timing([r['answer']['retrieval']['packing_seconds'] for r in completed]),
            'coverage': {key: statistics.mean(r['coverage'][key] for r in completed if r['coverage'][key] is not None)
                         for key in ['annotated_char_recall', 'full_evidence_recall']},
            'mean_evidence_tokens': statistics.mean(r['answer']['retrieval']['evidence_tokens'] for r in completed),
        }
    with (report / 'summary.json').open('x') as output:
        json.dump(summary, output, indent=2)
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    run()
