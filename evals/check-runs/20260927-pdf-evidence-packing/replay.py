"""Replay fixed production-selected candidates through packing, without providers."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
from time import perf_counter

from knowledgebase.rag.context import build_context
from knowledgebase.rag.packing import pack_evidence
from knowledgebase.rag.pdf_evidence import pdf_evidence
from knowledgebase.rag.pdf_models import PdfExtraction
from knowledgebase.schemas import RetrievedChunk, RetrievalDiagnostics, StructuredChunk

ROOT = Path(__file__).parent
LIVE = Path('evals/library-runs/20260927-v2-pdf-live')
INDEX = json.loads((LIVE/'index-snapshot.json').read_text())
FILES = {d['file']['file_id']: d for d in INDEX['files']}
PDFS = {i: PdfExtraction.model_validate(d['extraction']) for i,d in FILES.items()}
CHUNKS = {c['chunk_id']: c for d in INDEX['files'] for c in d['chunks']}
PARENTS = {c['parent_id']: c for d in INDEX['files'] for c in d['parents']}
CASES = json.loads((LIVE/'effective-cases.json').read_text())


def freeze():
    rows = [json.loads(line) for line in (LIVE/'repair-1/server-observations.jsonl').read_text().splitlines()]
    frozen = []
    for case in CASES['cases']:
        for arm in ['single','planned']:
            request_id=case['id']+'-'+arm
            last=next(r for r in reversed(rows) if r['request']==request_id and r['kind']=='stage')
            result=last['result']
            if arm=='single':
                candidates=result['diagnostics']['candidates'];diagnostics=result['diagnostics']
            else:
                candidates=result['evidence']['diagnostics']['candidates'];diagnostics=result['evidence']['diagnostics']
            selected=[]
            for c in candidates:
                document=FILES[c['file_id']]
                selected.append(RetrievedChunk(chunk=StructuredChunk.model_validate(CHUNKS[c['chunk_id']]),
                    file_name=document['file']['file_name'],document_labels=[Path(document['file']['file_name']).stem],
                    parent_id=c['parent_id'],matched_child_ids=[c['chunk_id']],
                    distance=c['distance'],fusion=c['fusion'],rerank=c['rerank']).model_dump(mode='json'))
            frozen.append(dict(case_id=case['id'],arm=arm,question=case['question'],facts=case['expected_fact_ids'],
                               selected=selected,diagnostics=diagnostics))
    write('frozen-inputs.json',dict(source='../../library-runs/20260927-v2-pdf-live/repair-1/server-observations.jsonl',
        corpus_sha256=sha256((LIVE/'index-snapshot.json').read_bytes()).hexdigest(),
        cases_sha256=sha256((LIVE/'effective-cases.json').read_bytes()).hexdigest(),rows=frozen))


def write(name, value):
    path=ROOT/name
    assert not path.exists(), 'Use a new output name; records are append-only.'
    path.write_text(json.dumps(value,indent=2)+'\n')


def replay(name):
    frozen=json.loads((ROOT/'frozen-inputs.json').read_text());results=[]
    for row in frozen['rows']:
        selected=[RetrievedChunk.model_validate({**c,'chunk':StructuredChunk.model_validate(CHUNKS[c['chunk']['chunk_id']])}) for c in row['selected']]
        regions={}
        for child in selected:
            parent_id=child.parent_id
            if parent_id is None:
                regions[child.chunk.chunk_id]=child.model_copy(deep=True)
            elif parent_id in regions:
                regions[parent_id].matched_child_ids.append(child.chunk.chunk_id)
            else:
                parent=PARENTS[parent_id]
                regions[parent_id]=child.model_copy(update={'chunk':StructuredChunk(chunk_id=parent_id,**{k:v for k,v in parent.items() if k!='parent_id'}),
                                                           'matched_child_ids':[child.chunk.chunk_id]})
        start=perf_counter()
        for hit in [*selected,*regions.values()]:
            hit.pdf=pdf_evidence(PDFS[hit.chunk.file_id],hit.chunk.start_offset,hit.chunk.end_offset)
        result=pack_evidence(selected,list(regions.values()),RetrievalDiagnostics.model_validate(row['diagnostics']))
        seconds=perf_counter()-start
        context=build_context(result.chunks)
        results.append(dict(case_id=row['case_id'],arm=row['arm'],question=row['question'],facts=row['facts'],
            selected_ids=[c.chunk.chunk_id for c in selected],seconds=seconds,result=result.model_dump(mode='json'),context=context))
    write(name+'.json',dict(frozen_sha256=sha256((ROOT/'frozen-inputs.json').read_bytes()).hexdigest(),
        code_hashes={str(p):sha256(p.read_bytes()).hexdigest() for p in Path('knowledgebase').rglob('*.py')},rows=results))
    print(f'Replayed {len(results)} frozen candidate sets without API calls.')
    for r in results:
        if r['case_id'] in ['apple-sales','apple-income','apparent-conflict']:
            print(r['case_id'],r['arm'],r['result']['diagnostics']['evidence_tokens'],
                  [(h['chunk']['chunk_id'].split(':')[-2:],h['chunk']['start_offset'],h['chunk']['end_offset']) for h in r['result']['chunks']])


if __name__=='__main__':
    freeze() if sys.argv[1]=='freeze' else replay(sys.argv[1])
