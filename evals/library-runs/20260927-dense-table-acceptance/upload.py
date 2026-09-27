"""Upload the unchanged PDF once; retain searchable source and index snapshots."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter

import httpx

ROOT=Path(__file__).resolve().parent
BASE='http://127.0.0.1:8786'
SOURCE=Path('evals/materials/pdf-v2/background-checks.pdf')
assert not (ROOT/'ingestion.json').exists()
record={'source_sha256':sha256(SOURCE.read_bytes()).hexdigest(),'source_bytes':SOURCE.stat().st_size,
        'at':datetime.now(timezone.utc).isoformat(),'status':'running','request_id':'upload-background','retries':0}
started=perf_counter()
try:
    with httpx.Client(timeout=240,trust_env=False) as client:
        assert client.get(BASE+'/api/files').json()==[]
        response=client.post(BASE+'/api/files',files={'file':(SOURCE.name,SOURCE.read_bytes(),'application/pdf')},headers={'x-eval-id':'upload-background'})
        record.update(http_status=response.status_code,upload_to_response_seconds=perf_counter()-started,response=response.json())
        response.raise_for_status()
        assert response.json()['status']=='ready'
        snapshot=client.get(BASE+'/__eval__/snapshot').json()
        (ROOT/'index-snapshot.json').write_text(json.dumps(snapshot,indent=2)+'\n')
        assert len(snapshot['files'])==1
        file=snapshot['files'][0]
        assert file['extraction']['source_hash']==record['source_sha256']
        record.update(status='completed',file_id=file['file']['file_id'],child_count=len(file['chunks']),parent_count=len(file['parents']),
            extraction_revision=file['extraction']['revision_id'],index_bytes=snapshot['index_bytes'],
            page_count=len(file['extraction']['pages']),
            snapshot_sha256=sha256((ROOT/'index-snapshot.json').read_bytes()).hexdigest())
        print(f"Upload ready: {record['child_count']} children, {record['parent_count']} parents, {record['upload_to_response_seconds']:.3f} seconds.")
except Exception as error:
    record.update(status='error',error_type=type(error).__name__)
    raise
finally:
    record['command_seconds']=perf_counter()-started
    (ROOT/'ingestion.json').write_text(json.dumps(record,indent=2)+'\n')
