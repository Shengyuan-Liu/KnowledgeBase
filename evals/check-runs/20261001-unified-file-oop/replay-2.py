"""Compare frozen PDF parsing, chunking, lexical ranking and supplied evidence."""

from hashlib import sha256
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, sys.argv[1])
from docling_core.types.doc import DoclingDocument
from knowledgebase import schemas
from knowledgebase.config import RetrievalOptions
from knowledgebase.rag.bm25 import search_bm25
from knowledgebase.rag.chunking import split_parent_child
from knowledgebase.rag.context import build_context
from knowledgebase.rag.pdf import adapt_pdf_document
from knowledgebase.rag.pdf_chunking import join_heading_parents
from knowledgebase.rag.pdf_evidence import table_rows
from knowledgebase.rag.retrieval import pack_retrieval_candidates
from knowledgebase.storage.database import build_engine, build_session_factory, init_db
from knowledgebase.storage.operations import create_file, save_parent_child_chunks, save_pdf_source

FIXTURES = ROOT / 'evals/check-runs/20260926-pdf-parser-selection'
INPUTS = ROOT / 'evals/check-runs/20260927-pdf-evidence-packing/frozen-inputs.json'
IDENTITY = schemas.PdfParserIdentity(package_versions=(("docling", "2.130.0"),),
                                    settings_json='{"do_ocr":false}', model_file_hashes=())
NEW = hasattr(schemas, 'File')
engine = build_engine('sqlite:///:memory:')
init_db(engine)
sessions = build_session_factory(engine)
output = {'inputs': {}, 'documents': [], 'queries': []}
children = []

def digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def chunk_data(chunk, parent=False):
    data = chunk.model_dump(mode='json')
    if parent and not NEW:
        data['chunk_id'] = data.pop('parent_id')
    data.pop('type', None)
    if parent:
        data.pop('parent_id', None)
    return data


for name in ['apple-fy24', 'ml-lecture', 'doclaynet', 'docling-report', 'background-checks']:
    path = FIXTURES / ('apple-1' if name == 'apple-fy24' else 'attempt-1') / f'{name}-docling.json'
    original = ROOT / f'evals/materials/pdf-v2/{name}.pdf'
    for source in (path, original):
        output['inputs'][str(source.relative_to(ROOT))] = sha256(source.read_bytes()).hexdigest()
    started = time.perf_counter()
    file = adapt_pdf_document(DoclingDocument.model_validate_json(path.read_text()), original.read_bytes(), IDENTITY)
    extraction = file.extraction_data() if NEW else file.model_dump(mode='json')
    batch = split_parent_child(file.text, file.blocks if NEW else file.source_blocks(), name,
                               parent_max_tokens=1536, child_max_tokens=512,
                               encoding_name='cl100k_base', table_row_spans=table_rows(file))
    batch = join_heading_parents(file, batch)
    output['documents'].append({
        'name': name, 'extraction_sha256': digest(extraction), 'revision_id': file.revision_id,
        'parents': [chunk_data(c, True) for c in batch.parents],
        'children': [chunk_data(c) for c in batch.children],
        'local_adapter_and_chunk_seconds': time.perf_counter() - started,
    })
    children.extend(batch.children)
    with sessions.begin() as session:
        create_file(session, name, name + '.pdf')
        save_pdf_source(session, name, file, {'strategy': 'parent_child'})
        save_parent_child_chunks(session, batch)

output['inputs'][str(INPUTS.relative_to(ROOT))] = sha256(INPUTS.read_bytes()).hexdigest()
questions = list(dict.fromkeys(row['question'] for row in json.loads(INPUTS.read_text())['rows']))
by_id = {c.chunk_id: c for c in children}
for question in questions:
    started = time.perf_counter()
    ranking = search_bm25(question, children, top_k=20)
    hits = [schemas.RetrievedChunk(chunk=by_id[m.chunk_id], file_name=by_id[m.chunk_id].file_id + '.pdf',
                                  distance=None, parent_id=by_id[m.chunk_id].parent_id,
                                  matched_child_ids=[m.chunk_id]) for m in ranking[:5]]
    with sessions() as session:
        result = pack_retrieval_candidates(hits, session, schemas.RetrievalDiagnostics(
            max_tokens=4096, tokenizer='cl100k_base', options=RetrievalOptions(packing_strategy='parent_then_child')))
    supplied = result.model_dump(mode='json')
    for item in supplied['chunks']:
        item['chunk'].pop('type', None)
        item['chunk'].pop('parent_id', None)
    output['queries'].append({'question': question, 'ranking': [m.model_dump() for m in ranking],
                              'supplied': supplied, 'context': build_context(result.chunks),
                              'local_search_and_pack_seconds': time.perf_counter() - started})
engine.dispose()
Path(sys.argv[2]).write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
print(f"Replayed {len(output['documents'])} PDFs and {len(questions)} frozen questions.")
