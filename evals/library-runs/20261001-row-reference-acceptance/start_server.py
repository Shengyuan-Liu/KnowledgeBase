"""Start one recorded local server with the frozen runtime, preserving logs."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import httpx

from clone_index import DATA, SOURCE, manifest

ROOT = Path(__file__).resolve().parent
assert (ROOT/'preparation.json').exists()
assert not (ROOT/'server-start.json').exists()
preparation = json.loads((ROOT/'preparation.json').read_text())
assert preparation['code_commit'] == subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
assert all(sha256(Path(p).read_bytes()).hexdigest() == digest for p, digest in preparation['production_hashes'].items())
assert sha256(Path('.env').read_bytes()).hexdigest() == preparation['env_file_sha256']
assert all(sha256((ROOT/name).read_bytes()).hexdigest() == digest for name, digest in preparation['harness_hashes'].items())
reuse = json.loads((ROOT/'index-reuse.json').read_text())
assert manifest(SOURCE) == reuse['source_file_hashes']
assert manifest(DATA) == reuse['source_file_hashes']
baseline = json.loads((ROOT/'baseline-index-snapshot.json').read_text())
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
                assert [item['file_id'] for item in response.json()] == [item['file']['file_id'] for item in baseline['files']]
                snapshot_response = client.get('http://127.0.0.1:8786/__eval__/snapshot')
                snapshot_response.raise_for_status()
                snapshot = snapshot_response.json()
                assert snapshot['files'] == baseline['files'], 'Frozen files, extraction, chunks or parents changed.'
                (ROOT/'startup-index-snapshot.json').write_text(json.dumps(snapshot,indent=2)+'\n')
                (ROOT/'server-ready.json').write_text(json.dumps({
                    'at':datetime.now(timezone.utc).isoformat(), 'seconds':time.perf_counter()-start,
                    'baseline_files_extraction_chunks_parents_equal':True,
                    'baseline_source_unchanged':manifest(SOURCE) == reuse['source_file_hashes'],
                    'upload_performed':False,
                },indent=2)+'\n')
                print(f'Server ready with the unchanged copied PDF index after {time.perf_counter()-start:.3f} seconds; PID {process.pid}. No upload or embedding preparation calls.')
                break
        except httpx.ConnectError:
            pass
        time.sleep(1)
    else:
        raise TimeoutError('Server readiness not established; inspect retained startup record.')
