"""Verify request identity, runtime, isolation and history parity without scoring answers."""
from hashlib import sha256
import json
from pathlib import Path
import socket

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clone_index import SOURCE, database_tables, manifest

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT.parent / '20260927-table-cell-context-acceptance'
preparation = json.loads((ROOT / 'preparation.json').read_text())
runtime = json.loads((ROOT / 'resolved-runtime.json').read_text())
baseline_runtime = json.loads((BASELINE / 'resolved-runtime.json').read_text())
assert runtime['settings'] == preparation['settings']
assert runtime['code_commit'] == preparation['code_commit']
assert runtime['source_hashes'] == preparation['production_hashes']
assert runtime['reranker'] == baseline_runtime['reranker']
assert runtime['packages'] == baseline_runtime['packages']
assert runtime['harness_hashes'] == preparation['harness_hashes']
assert sha256(Path('.env').read_bytes()).hexdigest() == preparation['env_file_sha256']
reuse = json.loads((ROOT / 'index-reuse.json').read_text())
assert manifest(SOURCE) == reuse['source_file_hashes']
baseline_snapshot = json.loads((ROOT / 'baseline-index-snapshot.json').read_text())
snapshot = json.loads((ROOT / 'index-snapshot.json').read_text())
assert snapshot['files'] == baseline_snapshot['files']
old_ids = {row[0] for row in database_tables(SOURCE)['conversations']}
new_ids = set()
rows = []
for case in json.loads((ROOT / 'frozen-cases.json').read_text())['cases']:
    for arm in ['single', 'planned']:
        row = json.loads((ROOT / f"{case['id']}-{arm}.json").read_text())
        assert row['request']['question'] == case['question']
        assert 'conversation_id' not in row['request']
        if row['status'] != 'completed':
            assert row['status'] in {'error', 'incomplete'}
            rows.append(row)
            continue
        assert row['http_status'] == 200
        assert row['history_matches'] and row['history_retrieval_matches']
        assert row['history_sources_shared_fields_match'] and row['history_sources_have_only_expected_schema_extra']
        assert ''.join(event['data'].get('delta', '') for event in row['events'] if event['data']['event'] == 'answer_delta') == row['answer']['answer']
        new_ids.add(row['answer']['conversation_id'])
        rows.append(row)
assert len(rows) == 6 and len(new_ids) == sum(row['status'] == 'completed' for row in rows) and not new_ids & old_ids
observations = [json.loads(line) for line in (ROOT / 'server-observations.jsonl').read_text().splitlines()]
sdk_calls = [item for item in observations if item['kind'] == 'sdk_start']
assert all(item['request'] in {f"{row['case_id']}-{row['arm']}" for row in rows} for item in sdk_calls)
stopped = json.loads((ROOT / 'server-stop.json').read_text())
assert stopped['port_closed'] and stopped['ownership_lock_released']
assert stopped['baseline_directory_unchanged'] and stopped['historical_rows_preserved'] and stopped['indexed_database_tables_unchanged']
with socket.socket() as connection:
    assert connection.connect_ex(('127.0.0.1', 8786)) != 0
result = {
    'intended_requests': len(rows), 'completed_requests': len(new_ids), 'failed_requests': sum(row['status'] != 'completed' for row in rows), 'distinct_fresh_conversations': len(new_ids),
    'launch_commit': runtime['code_commit'], 'runtime_matches_preparation': True,
    'baseline_reranker_and_packages_equal': True, 'frozen_snapshot_equal': True,
    'baseline_directory_unchanged': True, 'env_unchanged': True,
    'completed_answer_delta_and_history_contracts_match': True, 'all_request_outcomes_retained': True, 'shutdown_verified': True,
    'provider_calls': len(sdk_calls), 'provider_calls_for_preparation': 0,
    'quality_scored': False,
}
assert not (ROOT / 'run-integrity.json').exists()
(ROOT / 'run-integrity.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
