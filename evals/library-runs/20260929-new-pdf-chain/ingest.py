"""Restore the four-page financial fixture only in the cloned evaluation library."""
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter

import httpx

from clone_index import DATA, database_tables
from run import BASE, FROZEN, write

ROOT = Path(__file__).resolve().parent

if __name__ == '__main__':
    with httpx.Client(timeout=240, trust_env=False) as client:
        before = client.get(BASE + '/__eval__/snapshot').json()
        assert 'apple-fy24.pdf' not in [d['file']['file_name'] for d in before['files']]
        source = Path('evals/materials/pdf-v2/apple-fy24.pdf')
        started = perf_counter()
        response = client.post(BASE + '/api/files', files={'file': (source.name, source.read_bytes(), 'application/pdf')},
                               headers={'x-eval-id': 'ingest-apple'})
        row = dict(http_status=response.status_code, seconds=perf_counter()-started, result=response.json(),
                   index_bytes_before=before['index_bytes'])
        write('ingest-apple.json', row)
        response.raise_for_status()
        assert row['result']['status'] == 'ready'
        snapshot = client.get(BASE + '/__eval__/snapshot').json()
        write('index-snapshot.json', snapshot)
        rows = []
        for document in FROZEN['corpus']:
            indexed = next(d for d in snapshot['files'] if d['file']['file_name'] == document['file'])
            file_id = indexed['file']['file_id']
            revision = indexed['extraction']['revision_id']
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
        assert all(r['matches'] and r['byte_range_matches'] and r['wrong_revision_status'] == 409 for r in rows)
        write('post-ingest-table-hashes.json', {name: sorted(sha256(json.dumps(row).encode()).hexdigest() for row in rows)
                                                for name, rows in database_tables(DATA).items()})
        print(f'Apple ready in {row["seconds"]:.3f}s; all three original PDFs, byte ranges and revision checks match.')
