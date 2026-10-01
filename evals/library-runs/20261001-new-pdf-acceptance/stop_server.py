"""Verify indexed content is unchanged and release both evaluation data directories."""
from datetime import datetime, timezone
import fcntl,json,os,signal,socket,sqlite3,subprocess,time
from pathlib import Path
import httpx
from prepare_2 import ROOT, DATA, write
with httpx.Client(timeout=30,trust_env=False) as client:
    final=client.get('http://127.0.0.1:8787/__eval__/snapshot').json()
assert final['files']==json.loads((ROOT/'index-snapshot.json').read_text())['files']
write('final-index-state.json',dict(index_bytes=final['index_bytes'],files_extraction_chunks_parents_unchanged=True,ready_files=len(final['files'])))
start=json.loads((ROOT/'server-start-2.json').read_text());pid=start['pid']
assert str(ROOT/'server_2.py') in subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True)
os.kill(pid,signal.SIGTERM)
for attempt in range(40):
    with socket.socket() as connection:
        closed=connection.connect_ex(('127.0.0.1',8787))!=0
    if closed:break
    time.sleep(.25)
assert closed
for directory in [DATA,Path('data/evals/20261001-new-pdf-acceptance').resolve()]:
    with (directory/'.owner.lock').open('r+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
databases={}
for p in DATA.rglob('*.sqlite3'):
    with sqlite3.connect(f'file:{p}?mode=ro',uri=True) as db:
        tables=[x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        databases[str(p.relative_to(DATA))]={n:db.execute(f'SELECT COUNT(*) FROM "{n}"').fetchone()[0] for n in tables if n in ['embeddings','collections','segments']}
with sqlite3.connect(f'file:{DATA / "knowledgebase.db"}?mode=ro',uri=True) as db:
    tables=[x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    databases['knowledgebase.db']={n:db.execute(f'SELECT COUNT(*) FROM "{n}"').fetchone()[0] for n in tables}
write('server-stop.json',dict(pid=pid,stopped_at=datetime.now(timezone.utc).isoformat(),port_closed=True,ownership_locks_released=True,indexed_content_unchanged=True,index_bytes_after_stop=sum(p.stat().st_size for p in DATA.rglob('*') if p.is_file()),database_row_counts=databases,data_dir=str(DATA)))
print('1 passed: indexed files/extraction/chunks/parents unchanged; server stopped; both evaluation ownership locks released.')
