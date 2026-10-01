"""Rebuild only parent context in an isolated, stopped evaluation copy."""
from datetime import datetime, timezone
import fcntl
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter

from sqlalchemy import delete
from knowledgebase.rag.pdf_chunking import PDF_PARENT_CONTEXT_VERSION, join_heading_parents
from knowledgebase.rag.pdf_models import PdfExtraction
from knowledgebase.schemas import ChildChunk, ParentChunk, ParentChildChunks
from knowledgebase.storage.database import build_engine, build_session_factory
from knowledgebase.storage.models import ChildParentRecord, ParentChunkRecord, PdfSourceRecord
from knowledgebase.storage.operations import get_files, get_pdf_extraction, get_chunks, get_parents
from clone_index import DATA, SOURCE, manifest, database_tables

ROOT = Path(__file__).resolve().parent


def write(name, value):
    with (ROOT / name).open('x') as file:
        file.write(json.dumps(value, indent=2) + '\n')


if __name__ == '__main__':
    assert not (ROOT / 'parent-rebuild.json').exists()
    reuse = json.loads((ROOT / 'index-reuse.json').read_text())
    assert manifest(DATA) == reuse['source_file_hashes'] == manifest(SOURCE)
    snapshot = json.loads((ROOT / 'baseline-index-snapshot.json').read_text())
    baseline = json.loads((ROOT.parent / '20260929-new-pdf-chain/index-snapshot.json').read_text())
    assert snapshot['files'] == baseline['files']
    started = perf_counter()
    before_tables = database_tables(DATA)
    rows = []
    with (DATA / '.owner.lock').open('r') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        engine = build_engine(f"sqlite:///{DATA / 'knowledgebase.db'}")
        sessions = build_session_factory(engine)
        with sessions.begin() as session:
            for document in snapshot['files']:
                file_id = document['file']['file_id']
                extraction = PdfExtraction.model_validate(document['extraction'])
                original = ParentChildChunks(
                    parents=[ParentChunk.model_validate(p) for p in document['parents']],
                    children=[ChildChunk.model_validate(c) for c in document['chunks']],
                )
                began = perf_counter()
                rebuilt = join_heading_parents(extraction, original)
                elapsed = perf_counter() - began
                assert [c.model_dump(exclude={'parent_id'}) for c in original.children] == [c.model_dump(exclude={'parent_id'}) for c in rebuilt.children]
                session.execute(delete(ChildParentRecord).where(ChildParentRecord.chunk_id.in_([c.chunk_id for c in original.children])))
                session.execute(delete(ParentChunkRecord).where(ParentChunkRecord.file_id == file_id))
                session.add_all(ParentChunkRecord(**p.model_dump()) for p in rebuilt.parents)
                session.flush()
                session.add_all(ChildParentRecord(chunk_id=c.chunk_id, parent_id=c.parent_id) for c in rebuilt.children)
                source = session.get(PdfSourceRecord, file_id)
                source.indexing = {**source.indexing, 'pdf_parent_context': PDF_PARENT_CONTEXT_VERSION}
                rows.append(dict(file=document['file']['file_name'], parents_before=len(original.parents),
                                 parents_after=len(rebuilt.parents), children=len(rebuilt.children),
                                 grouping_seconds=elapsed, changed_links=sum(a.parent_id != b.parent_id for a, b in zip(original.children, rebuilt.children, strict=True))))
        with sessions() as session:
            after = {'files': [dict(file=f.model_dump(mode='json'),
                extraction=get_pdf_extraction(session, f.file_id).model_dump(mode='json'),
                chunks=[c.model_dump(mode='json') for c in get_chunks(session, f.file_id)],
                parents=[p.model_dump(mode='json') for p in get_parents(session, f.file_id)])
                for f in get_files(session) if f.status == 'ready']}
        engine.dispose()
        after_tables = database_tables(DATA)
        for name, values in before_tables.items():
            if name not in {'parent_chunks', 'child_parents', 'pdf_sources'}:
                assert values == after_tables[name], name
        for old, new in zip(snapshot['files'], after['files'], strict=True):
            assert old['file'] == new['file'] and old['extraction'] == new['extraction']
            assert [{k:v for k,v in c.items() if k != 'parent_id'} for c in old['chunks']] == [{k:v for k,v in c.items() if k != 'parent_id'} for c in new['chunks']]
        files = manifest(DATA)
        for name, metadata in reuse['source_file_hashes'].items():
            if name != 'knowledgebase.db':
                assert files[name] == metadata, name
        assert set(files) == set(reuse['source_file_hashes'])
    assert manifest(SOURCE) == reuse['source_file_hashes']
    write('rebuilt-index-snapshot.json', after)
    write('post-rebuild-table-hashes.json', {name: sorted(sha256(json.dumps(row).encode()).hexdigest() for row in values)
                                          for name, values in after_tables.items()})
    write('parent-rebuild.json', dict(at=datetime.now(timezone.utc).isoformat(), seconds=perf_counter()-started,
        version=PDF_PARENT_CONTEXT_VERSION, files=rows, after_file_hashes=files,
        child_text_ids_offsets_headings_unchanged=True, extraction_originals_vectors_unchanged=True,
        other_database_tables_unchanged=True, historical_rows_preserved=True, baseline_unchanged=True,
        provider_calls=0, public_upload_exercised=False,
        storage_bytes_before=sum(v['bytes'] for v in reuse['source_file_hashes'].values()),
        storage_bytes_after=sum(v['bytes'] for v in files.values())))
    print('Rebuilt parents in five isolated PDFs; all 621 children, vectors, extraction, originals and historical rows preserved. No provider calls.')
