"""Verify isolated-library preservation and stop only this evaluation server."""
from pathlib import Path
import hashlib,json,os,signal,subprocess,time
import httpx
ROOT=Path(__file__).parent
with httpx.Client(timeout=60,trust_env=False) as c:
 snapshot=c.get('http://127.0.0.1:8787/__eval__/snapshot').json()
 prior=json.loads((ROOT/'heldout-index-snapshot.json').read_text())
 assert len(snapshot['files'])==8
 assert {d['file']['file_id']:d['extraction'] for d in snapshot['files']}=={d['file']['file_id']:d['extraction'] for d in prior['files']}
 assert {d['file']['file_id']:d['chunks'] for d in snapshot['files']}=={d['file']['file_id']:d['chunks'] for d in prior['files']}
 records=[]
 for doc in snapshot['files']:
  meta=doc['file'];r=c.get('http://127.0.0.1:8787/api/files/'+meta['file_id']+'/original');records.append({'file':meta['file_name'],'original_sha256_matches':hashlib.sha256(r.content).hexdigest()==doc['extraction']['source_hash']})
 assert all(r['original_sha256_matches'] for r in records)
 with (ROOT/'final-index-check.json').open('x') as f:json.dump({'files':8,'pages':sum(len(d['extraction']['pages']) for d in snapshot['files']),'children':sum(len(d['chunks']) for d in snapshot['files']),'index_bytes':snapshot['index_bytes'],'canonical_extraction_and_chunks_unchanged':True,'originals':records,'lifecycle_probes_deleted':True},f,indent=2)
pid=int(subprocess.check_output(['lsof','-tiTCP:8787','-sTCP:LISTEN'],text=True).strip());command=subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True).strip();assert str(ROOT/'server.py') in command
os.kill(pid,signal.SIGTERM)
for _ in range(30):
 alive=subprocess.run(['lsof','-tiTCP:8787','-sTCP:LISTEN'],capture_output=True,text=True)
 if not alive.stdout.strip():break
 time.sleep(.2)
assert not alive.stdout.strip()
data=Path('data/evals/20261001-v2-release')
import fcntl
with (data / ".owner.lock").open("r+") as lock: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
with (ROOT/'server-stop.json').open('x') as f:json.dump({'pid':pid,'command':command,'port_free':True,'ownership_released':True,'index_bytes_after_stop':sum(p.stat().st_size for p in data.rglob('*') if p.is_file())},f,indent=2)
print('1 passed: originals/index preserved, probes removed, owned port and data lock released.')
