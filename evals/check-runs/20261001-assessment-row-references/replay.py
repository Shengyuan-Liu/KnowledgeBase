"""Compare prompt rendering on the six frozen live contexts without model calls."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace
import tiktoken

from knowledgebase.rag.context import build_context
from knowledgebase.rag.generation import _answer_messages
from knowledgebase.rag.sufficiency import ASSESSMENT_INSTRUCTIONS, SufficiencyAssessment, assessment_context, assessment_excerpts
from knowledgebase.schemas import RetrievedChunk, StructuredChunk

ROOT=Path(__file__).resolve().parent
LIVE=Path('evals/library-runs/20260929-pdf-heading-acceptance')
ROW=re.compile(r'^Row \d+:\d+ .* \(canonical offsets (\d+):(\d+)\):')
MARKERS=re.compile(r'(?m)^(?:\[p\d+\])+ ')


def capture(phase):
    frozen=json.loads((ROOT/'frozen-inputs.json').read_text())
    assert all(sha256(Path(p).read_bytes()).hexdigest()==digest for p,digest in frozen['files'].items())
    cases=json.loads((LIVE/'frozen-cases.json').read_text())['cases']
    encoding=tiktoken.get_encoding('cl100k_base')
    rows=[]
    for case in cases:
        raw=json.loads((LIVE/(case['id']+'-planned.json')).read_text())
        answer=raw['answer']
        chunks=[RetrievedChunk(file_name=s['file_name'],distance=s['distance'],pdf=s['pdf'],document_labels=s['document_labels'],
            chunk=StructuredChunk.model_validate({**s,'index':i})) for i,s in enumerate(answer['sources'])]
        result=SimpleNamespace(evidence=SimpleNamespace(chunks=chunks))
        catalog=assessment_excerpts(result)
        assessment=answer['retrieval']['planning']['assessment']
        assert catalog==assessment['evidence_catalog']
        context=assessment_context(result,catalog)
        assert MARKERS.sub('',context)==build_context(chunks)==assessment['context']
        record=assessment['record']
        payload=json.loads(next(m['content'] for m in record['input'] if m['role']=='user'))
        if phase=='before':
            assert context==payload['context']
        payload['context']=context
        prompt=ASSESSMENT_INSTRUCTIONS
        messages=[{'role':'developer','content':prompt},{'role':'user','content':json.dumps(payload,ensure_ascii=False)}]
        from knowledgebase.providers.limits import input_tokens as count_input_tokens
        input_tokens=count_input_tokens({'messages':messages,'schema':SufficiencyAssessment.model_json_schema()},'cl100k_base')
        if phase=='before':
            assert messages==record['input'] and input_tokens==record['input_token_count']
        assert input_tokens<=record['max_input_tokens']
        table_rows=[]
        for hit in chunks:
            for table in hit.pdf.tables if hit.pdf else []:
                for line in (table.reading or '').splitlines():
                    match=ROW.match(line)
                    assert match
                    start,end=map(int,match.groups())
                    ids=[e['evidence_id'] for e in catalog if e['file_id']==hit.chunk.file_id and e['start_offset']<end and start<e['end_offset']]
                    prefix=''.join(f'[{i}]' for i in ids)+' ' if ids else ''
                    table_rows.append(dict(file_id=hit.chunk.file_id,line=line,expected_ids=ids,
                        markers_present=bool(ids) and prefix+line in context))
        rows.append(dict(case_id=case['id'],assessment_context=context,catalog=catalog,
            assessment_messages=messages,assessment_input_tokens=input_tokens,assessment_input_cap=record['max_input_tokens'],
            table_rows=table_rows,answer_messages=_answer_messages(case['question'],chunks,assessment=assessment),
            answer_context=build_context(chunks),answer_context_tokens=len(encoding.encode_ordinary(build_context(chunks)))))
    target=ROOT/(phase+'.json')
    with target.open('x') as file:
        file.write(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),phase=phase,rows=rows),indent=2)+'\n')
    print(phase, 'contexts:',len(rows),'table readings:',sum(len(r['table_rows']) for r in rows),
        'with correct explicit IDs:',sum(s['markers_present'] for r in rows for s in r['table_rows']))
    print('Assessment input tokens:',[(r['case_id'],r['assessment_input_tokens']) for r in rows])


if __name__=='__main__':
    capture(sys.argv[1])
