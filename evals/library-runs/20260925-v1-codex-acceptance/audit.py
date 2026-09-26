"""Verify exact sources, frozen criteria, prompt isolation and review artifacts."""
from copy import deepcopy
import json
from pathlib import Path
import re
from evals import metrics
from evals.automatic import load_benchmark
from evals.evaluate import digest,read_jsonl,timestamp,write_json
from knowledgebase.rag.generation import _answer_messages,ANSWER_INSTRUCTIONS
from knowledgebase.schemas import RetrievedChunk,StructuredChunk
DIR=Path(__file__).parent
if __name__=='__main__':
    checks=[];frozen=json.loads((DIR/'freeze.json').read_text());run=json.loads((DIR/'run.json').read_text())
    assert digest((DIR/'PLAN.md').read_bytes())==run['plan_sha256']
    for kind in ('cases','corpus'):assert digest((DIR/f'{kind}.json').read_bytes())==frozen[f'{kind}_sha256']
    assert digest(ANSWER_INSTRUCTIONS.encode())==frozen['prompt_sha256']
    checks.append('Questions, corpus, criteria and generation prompt unchanged after freezing.')
    _,_,documents=load_benchmark();cases={c['id']:c for c in json.loads((DIR/'cases.json').read_text())}
    answers=read_jsonl(DIR/'answers.jsonl');calls=read_jsonl(DIR/'calls.jsonl')
    assert len(answers)==8 and len(calls)==33 and all(a['status']=='ok' for a in answers+calls)
    assert {stage:sum(c['stage']==stage for c in calls) for stage in ('ingestion','query_embedding','generation')}=={'ingestion':17,'query_embedding':8,'generation':8}
    checks.append('All 8 requests and 33 provider calls retained; no extra judge or retry calls.')
    generation={c['case_id']:c for c in calls if c['stage']=='generation'}
    for a in answers:
        for s in a['sources']:
            assert documents[s['file_name']][s['start_offset']:s['end_offset']]==s['text']
        chunks=[RetrievedChunk(chunk=StructuredChunk(**{**s,'index':0}),file_name=s['file_name'],distance=s['distance']) for s in a['sources']]
        assert _answer_messages(cases[a['case_id']]['question'],chunks)==generation[a['case_id']]['messages']
        assert a['retrieval']['evidence_tokens']<=4096 and not a['citation_check']['invalid_source_ids']
    checks.append('Exact canonical source spans, evidence budget and citation IDs verified for every answer.')
    checks.append('Generator messages contain only unchanged developer instructions, the question and supplied sources; no evaluator reference/rubric injection.')
    reviews=json.loads((DIR/'manual-review.json').read_text())
    assert len(reviews)==8 and sum(len(r['claims']) for r in reviews)==38
    assert sum(r['pass'] for r in reviews)==7
    acceptance=json.loads((DIR/'acceptance.json').read_text());assert acceptance['status']=='failed' and len(acceptance['blockers'])==1
    checks.append('One qualification failure remains visible despite passing operational gates; 38 claims audited, no output repair.')
    docs=[DIR/'README.md',DIR/'REVIEW.md',DIR/'PLAN.md',Path('docs/v1/merge-readiness.md'),Path('docs/v1/README.md'),Path('docs/v1/v1-evaluation-plan.md'),Path('README.md')]
    links=0
    for path in docs:
        text=path.read_text();assert text.count('```')%2==0
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if '://' in target or target.startswith('#'):continue
            assert (path.parent/target.split('#')[0]).exists(),(path,target)
            links+=1
    checks.append(f'Content, balanced code fences and {links} local report/doc link targets reviewed.')
    for path in DIR.iterdir():
        if path.is_file() and path.suffix in {'.json','.jsonl','.py','.md','.log'}:
            assert not re.search(r'\bsk-[A-Za-z0-9_-]{24,}',path.read_text()),path
    checks.append('No API-key-shaped secret in new text artifacts.')
    qualified=deepcopy(json.loads((DIR/'reviewed-metrics.json').read_text()))
    qualified['metrics']['rerank_seconds']=metrics.missing('Local reranking is disabled in this tested default configuration.',False)
    qualified['qualification_note']='Retains original automatic and reviewed summaries; clarifies disabled reranking latency as not applicable, not missing instrumentation.'
    write_json(DIR/'qualified-metrics.json',qualified)
    write_json(DIR/'audit.json',{'timestamp':timestamp(),'passed':len(checks),'checks':checks,'scope':'Artifact/data integrity and document review, separate from the failed semantic acceptance.'})
    print(len(checks),'passed; semantic acceptance remains failed on the recorded qualification.')
