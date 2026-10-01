"""Check whether the historical-context assertion already fails at the committed baseline."""
import difflib
import json
from pathlib import Path
import subprocess
from types import ModuleType

from knowledgebase.rag.generation import _answer_messages
from knowledgebase.schemas import RetrievedChunk, StructuredChunk

ROOT=Path(__file__).resolve().parent
case=json.loads(Path('evals/library-runs/20260927-financial-acceptance/apple-income-planned.json').read_text())
answer=case['answer']
chunks=[RetrievedChunk(file_name=s['file_name'],distance=s['distance'],pdf=s['pdf'],document_labels=s['document_labels'],
    chunk=StructuredChunk.model_validate({**s,'index':i})) for i,s in enumerate(answer['sources'])]
context=ModuleType('baseline_context')
exec(subprocess.check_output(['git','show','HEAD:knowledgebase/rag/context.py'],text=True),context.__dict__)
generation=ModuleType('baseline_generation')
exec(subprocess.check_output(['git','show','HEAD:knowledgebase/rag/generation.py'],text=True),generation.__dict__)
generation.build_context=context.build_context
old=generation._answer_messages(case['request']['question'],chunks,assessment=answer['retrieval']['planning']['assessment'])
new=_answer_messages(case['request']['question'],chunks,assessment=answer['retrieval']['planning']['assessment'])
assert old[0]==new[0]
historical=answer['retrieval']['planning']['assessment']['context']
current=context.build_context(chunks)
assert current!=historical
record=dict(baseline_user_message_equals_current=True,baseline_already_differs_from_historical_context=True,
    difference=list(difflib.unified_diff(historical.splitlines(),current.splitlines(),fromfile='retained historical context',tofile='committed baseline context',n=0)),
    conclusion='The failing assertion predates this change. Reuse the frozen source spans but compare prompt delivery with the current serializer; do not rewrite historical evidence.')
with (ROOT/'baseline-probe.json').open('x') as file:
    file.write(json.dumps(record,indent=2)+'\n')
print('\n'.join(record['difference']))
print('Baseline and current user messages are identical; historical serializer assertion is already stale. 1 passed')
