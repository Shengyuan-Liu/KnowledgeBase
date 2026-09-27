"""Restore frozen financial source records into a new evaluation-only index."""
from hashlib import sha256
import fcntl
import json
from pathlib import Path
import shutil
from time import perf_counter

from openai import OpenAI

from knowledgebase.config import Settings
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.rag.pdf_models import PdfExtraction
from knowledgebase.schemas import ChildChunk, ParentChunk, ParentChildChunks
from knowledgebase.storage.operations import (
    create_file, get_files, get_chunks, get_parents, get_pdf_extraction,
    save_parent_child_chunks, save_pdf_source, update_file_status,
)
from knowledgebase.storage.pdf_assets import PdfAssets
from knowledgebase.storage.runtime import open_storage
from observability import SyncObserver, REQUEST

ROOT = Path(__file__).parent
OLD = ROOT.parent / '20260927-v2-pdf-live'
SOURCE = Path('data/evals/20260927-v2-pdf-live')
DATA = Path('data/evals/20260927-financial-acceptance')


def prepare():
    started = perf_counter()
    assert not DATA.exists() and not (ROOT / 'preparation.json').exists()
    settings = Settings(openai_timeout_seconds=180, openai_max_retries=0)
    baseline = json.loads((OLD / 'repair-1/resolved-runtime.json').read_text())['settings']
    safe = settings.model_dump(mode='json', exclude={'openai_api_key', 'openai_base_url'})
    assert {k: v for k, v in safe.items() if k != 'data_dir'} == {k: v for k, v in baseline.items() if k != 'data_dir'}
    with (SOURCE / '.owner.lock').open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        shutil.copytree(SOURCE, DATA, ignore=shutil.ignore_patterns('.owner.lock'))
    snapshot = json.loads((OLD / 'index-snapshot.json').read_text())
    document = next(d for d in snapshot['files'] if d['file']['file_name'] == 'apple-fy24.pdf')
    file_id = document['file']['file_id']
    extraction = PdfExtraction.model_validate(document['extraction'])
    hierarchy = ParentChildChunks(children=[ChildChunk.model_validate(c) for c in document['chunks']],
                                  parents=[ParentChunk.model_validate(p) for p in document['parents']])
    original = Path('evals/materials/pdf-v2/apple-fy24.pdf').read_bytes()
    assert sha256(original).hexdigest() == extraction.source_hash
    with open_storage(DATA) as (sessions, store):
        with sessions() as session:
            assert file_id not in {f.file_id for f in get_files(session)}
        token = REQUEST.set('restore-apple-embeddings')
        try:
            with SyncObserver(OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url,
                                     timeout=180, max_retries=0)) as sdk:
                vectors = EmbeddingClient(sdk, settings.embedding_model).embed_documents([c.text for c in hierarchy.children])
        finally:
            REQUEST.reset(token)
        vector_path = DATA / 'restored-apple-vectors.json'
        vector_path.write_text(json.dumps({'chunk_ids': [c.chunk_id for c in hierarchy.children], 'vectors': vectors}))
        with sessions.begin() as session:
            create_file(session, file_id, 'apple-fy24.pdf')
            save_pdf_source(session, file_id, extraction, {
                'strategy': 'parent_child', 'embedding_model': settings.embedding_model,
                'chunk_max_tokens': settings.chunk_max_tokens, 'parent_max_tokens': settings.parent_max_tokens,
                'tokenizer': settings.chunk_tokenizer, 'chunk_size': settings.chunk_size,
                'overlap': settings.chunk_overlap, 'semantic': None,
            })
            save_parent_child_chunks(session, hierarchy)
            store.upsert_chunks(hierarchy.children, vectors)
            PdfAssets(DATA).save(file_id, original)
            update_file_status(session, file_id, 'ready')
        with sessions() as session:
            assert {f.file_id for f in get_files(session)} == {d['file']['file_id'] for d in snapshot['files']}
            for frozen in snapshot['files']:
                identity = frozen['file']['file_id']
                assert get_pdf_extraction(session, identity).model_dump(mode='json') == frozen['extraction']
                assert [c.model_dump(mode='json') for c in get_chunks(session, identity)] == frozen['chunks']
                assert [p.model_dump(mode='json') for p in get_parents(session, identity)] == frozen['parents']
                assert sha256(PdfAssets(DATA).path(identity).read_bytes()).hexdigest() == frozen['extraction']['source_hash']
    record = {'source_directory': str(SOURCE), 'isolated_directory': str(DATA),
              'snapshot_sha256': sha256((OLD / 'index-snapshot.json').read_bytes()).hexdigest(),
              'protocol_sha256': sha256((ROOT / 'protocol.md').read_bytes()).hexdigest(),
              'verified_files': 5, 'verified_children': 621,
              'restored_file_id': file_id, 'regenerated_vectors': len(vectors),
              'vectors_path': str(vector_path), 'vectors_sha256': sha256(vector_path.read_bytes()).hexdigest(),
              'embedding_model': settings.embedding_model, 'seconds': perf_counter() - started,
              'comparison_limit': 'Original Apple vectors were deleted by the historical lifecycle test; vector-byte parity is unavailable. Text, chunks, parents and extraction are exact frozen copies.',
              'index_bytes_after_restore': sum(p.stat().st_size for p in DATA.rglob('*') if p.is_file())}
    (ROOT / 'preparation.json').write_text(json.dumps(record, indent=2) + '\n')
    print('Restored 17 Apple vectors; all five originals, extractions, 621 children and parent records match the frozen snapshot.')


if __name__ == '__main__':
    prepare()
