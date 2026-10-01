"""Ingest only sealed original held-out PDFs, preserving their exact source bytes."""
from pathlib import Path
from time import perf_counter
import hashlib,json
import httpx
ROOT=Path(__file__).parent
MATERIAL=Path('evals/materials/pdf-v2-closeout-heldout')
def write(n,v):
 with (ROOT/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
protocol=json.loads((MATERIAL/'protocol.json').read_text())
write('heldout-execution-freeze.json',{'protocol_sha256':hashlib.sha256((MATERIAL/'protocol.json').read_bytes()).hexdigest(),'product_hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('knowledgebase').rglob('*.py')},'source_hashes':{d['file']:d['sha256'] for d in protocol['sources']},'thresholds':protocol['gate'],'no_prior_application_calls_on_this_corpus':True})
with httpx.Client(timeout=240,trust_env=False) as c:
 for d in protocol['sources']:
  data=(MATERIAL/d['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==d['sha256'];start=perf_counter()
  r=c.post('http://127.0.0.1:8787/api/files',files={'file':(d['file'],data,'application/pdf')},headers={'x-eval-id':'ingest-'+d['file']})
  write('ingest-'+d['file']+'.json',{'http_status':r.status_code,'result':r.json(),'seconds':perf_counter()-start});r.raise_for_status();assert r.json()['status']=='ready'
  original=c.get('http://127.0.0.1:8787/api/files/'+r.json()['file_id']+'/original');assert original.content==data
  print(d['file'],'ready; original bytes match',flush=True)
 snap=c.get('http://127.0.0.1:8787/__eval__/snapshot').json();write('heldout-index-snapshot.json',snap)
 # The immutable annotated page is the ranking unit; final support remains semantic.
 facts=[]
 for fact in protocol['facts']:
  document=next(d for d in snap['files'] if d['file']['file_name']==fact['file'])
  relevant=[b for b in document['extraction']['blocks'] if any(r['page_index']+1==fact['physical_page'] for r in b['regions'])]
  facts.append({**fact,'file_id':document['file']['file_id'],'page_spans':[[b['start_offset'],b['end_offset']] for b in relevant], 'mapping_available':bool(relevant)})
 write('heldout-page-labels.json',{'facts':facts,'unit':'source physical page; relevant child intersects annotated page; page-level labels are intentionally coarse and are not semantic claim correctness'})
print('2 passed original-byte ingestions; page labels mapped before answer calls.')
