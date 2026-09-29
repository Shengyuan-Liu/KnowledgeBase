"""Stop only this evaluation server and verify its isolated storage is released."""
from datetime import datetime, timezone
import fcntl
from hashlib import sha256
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time

from clone_index import SOURCE, manifest, database_tables

ROOT=Path(__file__).resolve().parent
DATA=Path('data/evals/20260929-new-pdf-chain').resolve()
assert not (ROOT/'server-stop.json').exists()
start=json.loads((ROOT/'server-start.json').read_text())
pid=start['pid']
command=subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True).strip()
assert str(ROOT/'server.py') in command
os.kill(pid,signal.SIGTERM)
for attempt in range(20):
    with socket.socket() as connection:
        if connection.connect_ex(('127.0.0.1',start['port'])) != 0:
            break
    time.sleep(0.25)
else:
    raise RuntimeError('Evaluation port is still listening.')
with (DATA/'.owner.lock').open('r+') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
reuse=json.loads((ROOT/'index-reuse.json').read_text())
assert manifest(SOURCE) == reuse['source_file_hashes'], 'Baseline files changed.'
baseline_tables = json.loads((ROOT/'post-ingest-table-hashes.json').read_text())
current_tables = {name: sorted(sha256(json.dumps(row).encode()).hexdigest() for row in rows)
                  for name, rows in database_tables(DATA).items()}
history_tables={'conversations','messages','answer_snapshots','retrieval_snapshots','sqlite_sequence'}
for name, rows in baseline_tables.items():
    if name == 'sqlite_sequence':
        continue
    if name in history_tables:
        assert set(map(repr, rows)) <= set(map(repr, current_tables[name])), f'Historical {name} rows changed.'
    else:
        assert current_tables[name] == rows, f'Indexed table {name} changed.'
record={'pid':pid,'signal':'SIGTERM','stopped_at':datetime.now(timezone.utc).isoformat(),
        'port_closed':True,'ownership_lock_released':True,
        'baseline_directory_unchanged':True, 'historical_rows_preserved':True,
        'indexed_database_tables_unchanged':True,
        'index_bytes_after_answers':sum(p.stat().st_size for p in DATA.rglob('*') if p.is_file())}
(ROOT/'server-stop.json').write_text(json.dumps(record,indent=2)+'\n')
print('Evaluation server stopped; port closed and isolated data ownership released.')
