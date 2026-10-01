"""Compare unchanged recorded inputs against baseline and repaired validators."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from types import ModuleType

from knowledgebase.rag import scope, sufficiency
from knowledgebase.rag.planning import AnswerRequirement
from knowledgebase.rag.planned_retrieval import PlannedEvidence
from knowledgebase.schemas import ScopeFile

ROOT=Path(__file__).resolve().parent
BASELINE='2e82744'
RUN=Path('evals/library-runs/20261001-new-pdf-acceptance')

def previous(module, path):
    source=subprocess.check_output(['git','show',f'{BASELINE}:{path}'],text=True)
    obj=ModuleType(module);sys.modules[module]=obj
    exec(compile(source,f'{BASELINE}:{path}','exec'),obj.__dict__)
    return obj

old_scope=previous('baseline_scope','knowledgebase/rag/scope.py')
old_assessment=previous('baseline_sufficiency','knowledgebase/rag/sufficiency.py')
fixture=json.loads(Path('tests/fixtures/new_pdf_scope_failures.json').read_text())
assert all(sha256(Path(p).read_bytes()).hexdigest()==digest for p,digest in fixture['provenance'].items())
catalog=[ScopeFile.model_validate(f) for f in fixture['catalog']]
finance=[]
for query in fixture['finance']['queries']:
    before=old_scope.resolve_document_scope(old_scope.document_references(query),catalog,file_ids=fixture['finance']['allowed_file_ids'])
    after=scope.resolve_document_scope(scope.document_references(query),catalog,file_ids=fixture['finance']['allowed_file_ids'])
    assert before.status=='not_found' and after.status=='resolved'
    assert after.file_ids==fixture['finance']['allowed_file_ids']
    finance.append(dict(query=query,before=before.model_dump(mode='json'),after=after.model_dump(mode='json')))
observations=[json.loads(line) for line in (RUN/'server-observations.jsonl').read_text().splitlines()]
starts={o['call_id']:o for o in observations if o['kind']=='sdk_start'}
rows=[]
for observation in observations:
    if observation['kind']!='sdk_complete':continue
    start=starts[observation['call_id']]
    if start['input'].get('text',{}).get('format',{}).get('name')!='evidence_assessment':continue
    result=PlannedEvidence.model_validate(next(o['result'] for o in observations if o['kind']=='stage' and o.get('stage')=='planned_retrieval' and o['request']==observation['request']))
    output=''.join(c['text'] for item in observation['result']['output'] for c in item.get('content',[]) if c.get('type')=='output_text')
    excerpts=sufficiency.assessment_excerpts(result)
    requirements=result.trace.plan.requirements
    try:
        normalized,queries=old_assessment.validate_assessment(old_assessment.SufficiencyAssessment.model_validate_json(output),requirements,excerpts)
        before=dict(status='validated',requirements=normalized,queries=queries)
    except ValueError as error:before=dict(status='error',message=str(error))
    normalized,queries,rejected=sufficiency.validate_assessment(sufficiency.SufficiencyAssessment.model_validate_json(output),requirements,excerpts)
    if before['status']=='validated':
        assert normalized==before['requirements'] and queries==before['queries'] and not rejected
    else:
        assert observation['request']=='retriever-training-restricted-planned'
        assert [r['status'] for r in normalized]==['supported','missing']
        assert len(rejected)==1 and queries==[]
    rows.append(dict(request=observation['request'],output_sha256=sha256(output.encode()).hexdigest(),before=before,after=dict(status='validated',requirements=normalized,queries=queries,rejected_queries=rejected),evidence_catalog_unchanged=True))
assert len(rows)==5
record=dict(at=datetime.now(timezone.utc).isoformat(),baseline_commit=BASELINE,source_artifacts=fixture['provenance'],current_source_hashes={p:sha256(Path(p).read_bytes()).hexdigest() for p in ['knowledgebase/rag/scope.py','knowledgebase/rag/sufficiency.py','knowledgebase/services/hops.py']},finance=finance,assessments=rows,provider_calls=0,summary=dict(financial_scopes_resolved_before=0,financial_scopes_resolved_after=4,financial_query_count=4,assessment_outputs_validated_before=4,assessment_outputs_validated_after=5,assessment_count=5,unchanged_successful_assessments=4,rejected_supplementary_proposals=1),limits=['Same frozen four-PDF inputs, questions, original annotations and recorded provider outputs. No answer or model-input repair.','Validator/scope replay only: no new ranking, packing, generated answer, live latency, provider usage or semantic acceptance score.','The financial case has no provider assessment because retrieval was empty in the original run; only its four real query scopes are replayed.','No actual dependent chain was executed; this change does not establish that gate.'])
with (ROOT/'comparison.json').open('x') as f:f.write(json.dumps(record,indent=2)+'\n')
print('2 passed: four original financial query scopes restored; five assessment outputs replayed, with one invalid proposal rejected and four prior successes unchanged. No provider calls.')
