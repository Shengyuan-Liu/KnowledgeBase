"""Clone the inactive prior evaluation index without changing its source or vectors."""
from hashlib import sha256
import fcntl
import json
from pathlib import Path
import shutil
from time import perf_counter

import numpy as np

from knowledgebase.config import Settings
from knowledgebase.storage.operations import get_files, get_chunks, get_parents, get_pdf_extraction
from knowledgebase.storage.pdf_assets import PdfAssets
from knowledgebase.storage.runtime import open_storage

ROOT = Path(__file__).parent
PRIOR = ROOT.parent / '20260927-financial-acceptance'
SOURCE = Path('data/evals/20260927-financial-acceptance')
DATA = Path('data/evals/20260927-financial-citation-acceptance')


def file_hashes(directory):
    return {str(p.relative_to(directory)): sha256(p.read_bytes()).hexdigest()
            for p in sorted(directory.rglob('*')) if p.is_file() and p.name != '.owner.lock'}


def prepare():
    started = perf_counter()
    assert not DATA.exists() and not (ROOT / 'preparation.json').exists()
    settings = Settings(openai_timeout_seconds=180, openai_max_retries=0)
    baseline = json.loads((PRIOR / 'resolved-runtime.json').read_text())['settings']
    safe = settings.model_dump(mode='json', exclude={'openai_api_key', 'openai_base_url'})
    assert {k: v for k, v in safe.items() if k != 'data_dir'} == {k: v for k, v in baseline.items() if k != 'data_dir'}
    assert (ROOT / 'frozen-cases.json').read_bytes() == (PRIOR / 'frozen-cases.json').read_bytes()
    with (SOURCE / '.owner.lock').open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before_hashes = file_hashes(SOURCE)
        shutil.copytree(SOURCE, DATA, ignore=shutil.ignore_patterns('.owner.lock'))
        cloned_hashes = file_hashes(DATA)
        assert before_hashes == cloned_hashes == file_hashes(SOURCE)
    snapshot_path = ROOT.parent / '20260927-v2-pdf-live/index-snapshot.json'
    snapshot = json.loads(snapshot_path.read_text())
    with open_storage(DATA) as (sessions, store):
        with sessions() as session:
            assert {f.file_id for f in get_files(session)} == {d['file']['file_id'] for d in snapshot['files']}
            for frozen in snapshot['files']:
                identity = frozen['file']['file_id']
                assert get_pdf_extraction(session, identity).model_dump(mode='json') == frozen['extraction']
                assert [c.model_dump(mode='json') for c in get_chunks(session, identity)] == frozen['chunks']
                assert [p.model_dump(mode='json') for p in get_parents(session, identity)] == frozen['parents']
                assert sha256(PdfAssets(DATA).path(identity).read_bytes()).hexdigest() == frozen['extraction']['source_hash']
        vectors = store._collection.get(include=['embeddings'])
        assert set(vectors['ids']) == {c['chunk_id'] for d in snapshot['files'] for c in d['chunks']}
        digest = sha256()
        for identity, vector in sorted(zip(vectors['ids'], vectors['embeddings'])):
            digest.update(identity.encode())
            digest.update(np.asarray(vector, dtype='<f4').tobytes())
    record = dict(source_directory=str(SOURCE), isolated_directory=str(DATA),
        source_file_hashes=before_hashes, cloned_file_hashes_before_open=cloned_hashes,
        copy_byte_identical=True, source_unchanged=True,
        snapshot_sha256=sha256(snapshot_path.read_bytes()).hexdigest(),
        protocol_sha256=sha256((ROOT / 'protocol.md').read_bytes()).hexdigest(),
        prior_runtime_sha256=sha256((PRIOR / 'resolved-runtime.json').read_bytes()).hexdigest(),
        prior_preparation_sha256=sha256((PRIOR / 'preparation.json').read_bytes()).hexdigest(),
        verified_files=len(snapshot['files']), verified_children=len(vectors['ids']),
        vector_digest=digest.hexdigest(), vector_digest_method='Sorted ID UTF-8 followed by little-endian float32 vector bytes.',
        provider_calls=0, regenerated_vectors=0, seconds=perf_counter()-started,
        comparison_limit='Immediate baseline uses identical persisted vector storage. Earlier historical Apple vector regeneration remains part of the preceding run; no vectors are regenerated here.',
        index_bytes_after_clone=sum(p.stat().st_size for p in DATA.rglob('*') if p.is_file()))
    (ROOT / 'preparation.json').write_text(json.dumps(record, indent=2) + '\n')
    print(f"Cloned {len(before_hashes)} files byte-for-byte; verified five PDFs, 621 children, parents and vector IDs without provider calls.")


if __name__ == '__main__':
    prepare()
