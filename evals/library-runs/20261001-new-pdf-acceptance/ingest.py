"""Upload each original exactly once, preserving failures and indexed extraction."""
from datetime import datetime, timezone
from hashlib import sha256
from time import perf_counter
import json
import httpx
from prepare import ROOT, MATERIAL, write
BASE='http://127.0.0.1:8787'
manifest=json.loads((MATERIAL/'manifest.json').read_text())
with httpx.Client(timeout=240,trust_env=False) as client:
    for doc in manifest['files']:
        identity='ingest-'+doc['file'].removesuffix('.pdf')
        assert not (ROOT/(identity+'.json')).exists()
        started=perf_counter();row=dict(file=doc['file'],at=datetime.now(timezone.utc).isoformat())
        try:
            response=client.post(BASE+'/api/files',files={'file':(doc['file'],(MATERIAL/doc['file']).read_bytes(),'application/pdf')},headers={'x-eval-id':identity})
            row.update(http_status=response.status_code,result=response.json())
        except Exception as error:row.update(error_type=type(error).__name__)
        row['seconds']=perf_counter()-started
        write(identity+'.json',row)
        print(identity,round(row['seconds'],2),row.get('result',{}).get('status',row.get('error_type')),flush=True)
    snapshot=client.get(BASE+'/__eval__/snapshot').json();write('index-snapshot.json',snapshot)
    originals=[]
    for doc in snapshot['files']:
        meta=doc['file'];revision=doc['extraction']['revision_id'];url=BASE+f"/api/files/{meta['file_id']}/original"
        response=client.get(url,params={'revision':revision})
        expected=next(f for f in manifest['files'] if f['file']==meta['file_name'])
        partial=client.get(url,params={'revision':revision},headers={'Range':'bytes=0-31'})
        wrong=client.get(url,params={'revision':'wrong-evaluation-revision'})
        originals.append(dict(file=meta['file_name'],file_id=meta['file_id'],revision=revision,http_status=response.status_code,sha256=sha256(response.content).hexdigest(),matches=sha256(response.content).hexdigest()==expected['sha256'],byte_range_matches=partial.status_code==206 and partial.content==response.content[:32],wrong_revision_status=wrong.status_code))
    write('original-access.json',originals)
    assert len(snapshot['files'])==4
    assert sum(len(d['extraction']['pages']) for d in snapshot['files'])==90
    assert all(r['matches'] and r['byte_range_matches'] and r['wrong_revision_status']==409 for r in originals)
    print('4 passed: all originals ready; 90 physical pages; original bytes, ranges and revision guards verified.')
