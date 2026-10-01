"""Confirm shutdown after the listening socket closes and lifespan cleanup finishes."""
from pathlib import Path
import fcntl,json,socket,time
ROOT=Path(__file__).parent;DATA=Path('data/evals/20261001-v2-release')
with socket.socket() as sock:assert sock.connect_ex(('127.0.0.1',8787))!=0
for _ in range(50):
 try:
  with (DATA/'.owner.lock').open('r+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  break
 except BlockingIOError:time.sleep(.2)
else:raise RuntimeError('Ownership still held')
with (ROOT/'server-stop.json').open('x') as f:json.dump({'port_free':True,'ownership_released':True,'index_bytes_after_stop':sum(p.stat().st_size for p in DATA.rglob('*') if p.is_file()),'note':'First check rejected relative versus absolute command spelling before sending a signal. Second sent SIGTERM; socket closed before lifespan cleanup released the lock. This read-only confirmation observes both terminal conditions.'},f,indent=2)
print('1 passed: owned server stopped, port free and data lock released.')
