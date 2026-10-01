"""Start one recorded local server with the frozen runtime, preserving logs."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import httpx

ROOT = Path(__file__).resolve().parent
assert (ROOT/'preparation.json').exists()
assert not (ROOT/'server-start.json').exists()
env=dict(os.environ, PYTHONPATH='.', HF_HUB_OFFLINE='1', OPENAI_TIMEOUT_SECONDS='180', OPENAI_MAX_RETRIES='0')
with (ROOT/'server.log').open('x') as log:
    process=subprocess.Popen([sys.executable,str(ROOT/'server.py')],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
record={'pid':process.pid,'command':[sys.executable,str(ROOT/'server.py')],'started_at':datetime.now(timezone.utc).isoformat(),
        'environment_overrides':{k:env[k] for k in ['PYTHONPATH','HF_HUB_OFFLINE','OPENAI_TIMEOUT_SECONDS','OPENAI_MAX_RETRIES']},
        'port':8786,'log':'server.log'}
(ROOT/'server-start.json').write_text(json.dumps(record,indent=2)+'\n')
start=time.perf_counter()
with httpx.Client(timeout=2,trust_env=False) as client:
    for attempt in range(45):
        if process.poll() is not None:
            raise RuntimeError('Server exited; retain and inspect server.log.')
        try:
            response=client.get('http://127.0.0.1:8786/api/files')
            if response.status_code == 200:
                assert response.json() == [], 'Index must start empty.'
                print(f'Server ready with an empty isolated library after {time.perf_counter()-start:.3f} seconds; PID {process.pid}.')
                break
        except httpx.ConnectError:
            pass
        time.sleep(1)
    else:
        raise TimeoutError('Server readiness not established; inspect retained startup record.')
