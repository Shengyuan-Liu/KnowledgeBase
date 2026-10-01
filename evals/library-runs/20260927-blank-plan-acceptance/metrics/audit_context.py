"""Audit actual SDK contexts and reproduce the recorded planner rejection offline."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys

import tiktoken
from knowledgebase.rag.context import build_context
from knowledgebase.rag.pdf_models import PdfExtraction
from knowledgebase.rag.planning import PlanDecision
from knowledgebase.schemas import RetrievedEvidence
from analyze import ROOT, DIRECTORY, final_result, read, records, write

helper = Path('evals/check-runs/20260927-blank-plan/compare.py')
spec = importlib.util.spec_from_file_location('reading_audit', helper)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
observations = records()
frozen = read(ROOT/'frozen-cases.json')
extraction = PdfExtraction.model_validate(read(ROOT/'index-snapshot.json')['files'][0]['extraction'])
encoding = tiktoken.get_encoding('cl100k_base')
rows = []
for case in frozen['cases']:
    for arm in ['single','planned']:
        identity=case['id']+'-'+arm
        raw=read(ROOT/(identity+'.json'))
        starts=[(i,event) for i,event in enumerate(observations,1) if event['kind']=='sdk_start'
                and event['request']==identity and event['api']=='responses' and event['input'].get('stream')]
        if raw['status'] != 'completed':
            assert not starts and final_result(observations,identity) is None
            rows.append(dict(identity=identity,status='unavailable',reason='Planner validation failed before retrieval or generation; no supplied context exists.'))
            continue
        assert len(starts)==1
        result=final_result(observations,identity)
        evidence=RetrievedEvidence.model_validate(result['evidence'] if 'trace' in result else result)
        line,event=starts[0]
        user=next(m['content'] for m in event['input']['input'] if m['role']=='user')
        actual=user.split('\n\nSources:\n',1)[1]
        assert actual==build_context(evidence.chunks)
        count=len(encoding.encode_ordinary(actual))
        assert count==evidence.diagnostics.evidence_tokens<=4096
        cells=module.audit(evidence,actual,extraction)
        path=DIRECTORY/(identity+'-actual-context.txt')
        with path.open('x') as output:output.write(actual)
        rows.append(dict(identity=identity,status='measured',sdk_line=line,sdk_call_id=event['call_id'],
            actual_context_sha256=sha256(actual.encode()).hexdigest(),actual_context_tokens=count,
            canonical_excerpts_pages_and_readings_preserved=True,audited_cell_bindings=cells,artifact=path.name))
write('actual-context-audit.json',dict(reviewer='Codex /root; mechanical audit, not independent semantic review',rows=rows,
    generation_calls=sum(r['status']=='measured' for r in rows),provider_calls_during_audit=0))
print('Audited all actual generation contexts without provider calls.')
