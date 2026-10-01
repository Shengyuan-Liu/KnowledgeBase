"""Freeze, ingest and exercise an unknown target once via the real SSE endpoint."""
import hashlib,json,time
from pathlib import Path
import httpx
import run
ROOT=Path(__file__).parent
MATERIAL=Path('evals/materials/pdf-v2-closeout-dependency')
protocol=json.loads((MATERIAL/'protocol.json').read_text())
run.write('dependency-freeze.json',{'inputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in MATERIAL.iterdir() if p.is_file()},'code':'d8108df','frozen_before_calls':True})
with httpx.Client(timeout=240,trust_env=False) as c:
 for name in protocol['questions'][0]['files']:
  start=time.perf_counter();r=c.post(run.BASE+'/api/files',files={'file':(name,(MATERIAL/name).read_bytes(),'application/pdf')},headers={'x-eval-id':'ingest-'+name});run.write('ingest-'+name+'.json',{'status':r.status_code,'result':r.json(),'seconds':time.perf_counter()-start});r.raise_for_status();assert r.json()['status']=='ready'
 snap=c.get(run.BASE+'/__eval__/snapshot').json();run.write('dependency-index-snapshot.json',snap)
 # Reuse the unchanged HTTP recorder with a dedicated directory and one case.
 import shutil
 dest=ROOT/'dependency';dest.mkdir();shutil.copy2(ROOT/'dependency-index-snapshot.json',dest/'index-snapshot.json');(dest/'frozen-labels.json').write_text(json.dumps(protocol['facts'])+'\n')
 source=(ROOT/'run.py').read_text().replace("assert len(FROZEN['cases']) == 6","assert len(FROZEN['cases']) == 1")
 scope={'__name__':'dependency_recorder','__file__':str(dest/'run.py')};exec(compile(source,str(dest/'run.py'),'exec'),scope)
 scope['FROZEN']={'cases':[{**protocol['questions'][0],'followup_of':None}]};scope['answers'](c)
print('1 completed dependency request; semantic and trace review pending.')
