"""Verify unchanged original PDFs and capture the copied live index before answers."""
from hashlib import sha256
import json
from pathlib import Path
import httpx
from run import BASE, FROZEN, write

ROOT = Path(__file__).resolve().parent

if __name__ == '__main__':
    with httpx.Client(timeout=30, trust_env=False) as client:
        response = client.get(BASE + '/__eval__/snapshot')
        response.raise_for_status()
        snapshot = response.json()
        assert snapshot['files'] == json.loads((ROOT/'baseline-index-snapshot.json').read_text())['files']
        write('index-snapshot.json', snapshot)
        rows = []
        for document in FROZEN['corpus']:
            indexed = next(d for d in snapshot['files'] if d['file']['file_name'] == document['file'])
            file_id, revision = indexed['file']['file_id'], indexed['extraction']['revision_id']
            url = BASE + f'/api/files/{file_id}/original'
            original = client.get(url, params={'revision': revision})
            partial = client.get(url, params={'revision': revision}, headers={'Range': 'bytes=0-31'})
            wrong = client.get(url, params={'revision': 'wrong-evaluation-revision'})
            rows.append(dict(file=document['file'], file_id=file_id, revision=revision,
                http_status=original.status_code, sha256=sha256(original.content).hexdigest(),
                matches=sha256(original.content).hexdigest() == document['sha256'],
                byte_range_matches=partial.status_code == 206 and partial.content == original.content[:32],
                wrong_revision_status=wrong.status_code))
        write('original-access.json', rows)
        assert all(r['http_status'] == 200 and r['matches'] and r['byte_range_matches'] and r['wrong_revision_status'] == 409 for r in rows)
    print('Three queried original PDFs match frozen bytes, ranges and revision guards; unchanged snapshot verified.')
