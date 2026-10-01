"""Stop only this evaluation server and verify its isolated storage is released."""
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time

ROOT=Path(__file__).resolve().parent
DATA=Path('data/evals/20260927-dense-table-acceptance').resolve()
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
record={'pid':pid,'signal':'SIGTERM','stopped_at':datetime.now(timezone.utc).isoformat(),
        'port_closed':True,'ownership_lock_released':True,
        'index_bytes_after_answers':sum(p.stat().st_size for p in DATA.rglob('*') if p.is_file())}
(ROOT/'server-stop.json').write_text(json.dumps(record,indent=2)+'\n')
print('Evaluation server stopped; port closed and isolated data ownership released.')
