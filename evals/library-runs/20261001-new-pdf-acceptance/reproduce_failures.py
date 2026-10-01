"""Replay the two observed failures locally without provider calls or repairs."""
import json
from knowledgebase.rag.planned_retrieval import PlannedEvidence
from knowledgebase.rag.sufficiency import SufficiencyAssessment, assessment_excerpts, validate_assessment
from knowledgebase.rag.scope import document_references, resolve_document_scope
from knowledgebase.schemas import ScopeFile
from prepare import ROOT, write
observations=[json.loads(line) for line in (ROOT/'server-observations.jsonl').read_text().splitlines()]
request='retriever-training-restricted-planned'
rows=[o for o in observations if o['request']==request]
result=PlannedEvidence.model_validate(next(o['result'] for o in rows if o['kind']=='stage'))
response=[o['result'] for o in rows if o['kind']=='sdk_complete' and o.get('result',{}).get('output')][-1]
raw=''.join(c['text'] for item in response['output'] for c in item.get('content',[]) if c.get('type')=='output_text')
decision=SufficiencyAssessment.model_validate_json(raw)
try:
    validate_assessment(decision,result.trace.plan.requirements,assessment_excerpts(result))
except ValueError as error:
    assert str(error)=='Question reformulations cannot contain an unbound target.'
    restricted=dict(error_type=type(error).__name__,message=str(error),proposal=decision.queries[0].model_dump(),supported_bridge_decision=decision.requirements[0].model_dump(),gap_decision=decision.requirements[1].model_dump(),allowed_file_ids=result.trace.allowed_file_ids,scope_preserved=all(set(run.requested_file_ids)<=set(result.trace.allowed_file_ids) and all(h.chunk.file_id in result.trace.allowed_file_ids for h in run.result.hits) for run in result.trace.runs),limitation='Exact retained output reproduces local validator error; live API exposed a generic processing failure, not a saved exception stack.')
else:raise AssertionError('Observed validator failure did not reproduce.')
finance=json.loads((ROOT/'income-period-basis-planned.json').read_text())['answer']['retrieval']['planning']['trace']
query=finance['runs'][0]['text'];references=document_references(query)
assert references==['relevant document']
file_id=finance['allowed_file_ids'][0]
scope=resolve_document_scope(references,[ScopeFile(file_id=file_id,file_name='nvidia-fy25.pdf',labels=['nvidia-fy25'])],file_ids=[file_id])
assert scope.status=='not_found' and scope.file_ids==[]
write('failure-reproduction.json',dict(restricted=restricted,finance=dict(query=query,references=references,scope=scope.model_dump(mode='json'),same_failure_in_all_four_live_queries=all(run['result']['diagnostics']['document_scope']['status']=='not_found' for run in finance['runs'])),provider_calls=0,product_changes=False))
print('2 passed: retained restricted assessment reproduces ValueError; financial query reproduces incorrect filename scope. No provider calls.')
