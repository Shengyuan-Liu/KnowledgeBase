"""Start a fresh isolated server once and preserve the empty-index snapshot."""
from datetime import datetime, timezone
from hashlib import sha256
import json, os, subprocess, sys, time
import httpx
from prepare import ROOT, DATA, write
p=json.loads((ROOT/'preparation.json').read_text())
assert not DATA.exists()
assert all(sha256(__import__('pathlib').Path(f).read_bytes()).hexdigest()==v for f,v in p['production_hashes'].items())
assert sha256(__import__('pathlib').Path('.env').read_bytes()).hexdigest()==p['env_file_sha256']
assert all(sha256((ROOT/f).read_bytes()).hexdigest()==v for f,v in p['harness_hashes'].items())
env=dict(os.environ,PYTHONPATH='.',HF_HUB_OFFLINE='1',OPENAI_TIMEOUT_SECONDS='180',OPENAI_MAX_RETRIES='0')
with (ROOT/'server.log').open('x') as log:
    process=subprocess.Popen([sys.executable,str(ROOT/'server.py')],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
write('server-start.json',dict(pid=process.pid,command=[sys.executable,str(ROOT/'server.py')],started_at=datetime.now(timezone.utc).isoformat(),port=8787,environment_overrides={k:env[k] for k in ['PYTHONPATH','HF_HUB_OFFLINE','OPENAI_TIMEOUT_SECONDS','OPENAI_MAX_RETRIES']}))
started=time.perf_counter()
with httpx.Client(timeout=2,trust_env=False) as client:
    for attempt in range(45):
        assert process.poll() is None,'Server exited; inspect preserved server.log.'
        try:
            response=client.get('http://127.0.0.1:8787/api/files')
            if response.status_code==200:
                assert response.json()==[]
                snapshot=client.get('http://127.0.0.1:8787/__eval__/snapshot').json()
                assert snapshot['files']==[]
                write('startup-index-snapshot.json',snapshot)
                write('server-ready.json',dict(at=datetime.now(timezone.utc).isoformat(),seconds=time.perf_counter()-started,empty_index=True))
                print('1 passed: fresh isolated server ready with zero files.');break
        except httpx.ConnectError:pass
        time.sleep(1)
    else: raise TimeoutError('Server readiness not established.')
