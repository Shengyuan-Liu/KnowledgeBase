"""Copy the stopped baseline index byte-for-byte while holding its owner lock."""
from datetime import datetime, timezone
import fcntl
from hashlib import sha256
import json
from pathlib import Path
import shutil
import socket
import sqlite3

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT.parent / '20260927-dense-table-acceptance'
SOURCE = Path('data/evals/20260927-dense-table-acceptance').resolve()
DATA = Path('data/evals/20260927-table-context-scope-acceptance').resolve()


def manifest(directory):
    return {str(p.relative_to(directory)): {'sha256': sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}
            for p in sorted(directory.rglob('*')) if p.is_file()}


def database_tables(directory):
    with sqlite3.connect(f'file:{directory / "knowledgebase.db"}?mode=ro&immutable=1', uri=True) as connection:
        names = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        return {name: sorted(connection.execute(f'SELECT * FROM "{name}"').fetchall(), key=repr) for name in names}


if __name__ == '__main__':
    assert not DATA.exists(), 'Preserve existing run data; do not overwrite.'
    assert not (ROOT / 'index-reuse.json').exists()
    stopped = json.loads((BASELINE / 'server-stop.json').read_text())
    assert stopped['port_closed'] and stopped['ownership_lock_released']
    with socket.socket() as connection:
        assert connection.connect_ex(('127.0.0.1', 8786)) != 0
    with (SOURCE / '.owner.lock').open('r') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before = manifest(SOURCE)
        assert not any(name.endswith(('-wal', '-shm', '-journal')) for name in before), 'Source database is not quiescent.'
        source_tables = database_tables(SOURCE)
        shutil.copytree(SOURCE, DATA)
        copied = manifest(DATA)
        assert copied == before == manifest(SOURCE)
        assert database_tables(DATA) == source_tables
    hashes = {name: sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest() for name, rows in source_tables.items()}
    record = {
        'at': datetime.now(timezone.utc).isoformat(),
        'source_directory': str(SOURCE), 'data_directory': str(DATA),
        'source_owner_lock_acquired': True, 'source_unchanged_after_copy': True,
        'byte_identical_copy': True, 'source_file_hashes': before,
        'source_table_hashes': hashes, 'source_table_counts': {name: len(rows) for name, rows in source_tables.items()},
        'baseline_snapshot_sha256': sha256((ROOT / 'baseline-index-snapshot.json').read_bytes()).hexdigest(),
        'ingestion': {'status': 'not_applicable', 'reason': 'Existing frozen extraction and embeddings copied; no parsing, upload or embedding call.'},
        'historical_conversations_preserved': True, 'new_requests_start_fresh_conversations': True,
        'provider_calls': 0,
    }
    (ROOT / 'index-reuse.json').write_text(json.dumps(record, indent=2) + '\n')
    print('Baseline owner lock acquired; isolated copy is byte-identical, including every database table and vector file. Baseline remains unchanged. No provider calls.')
