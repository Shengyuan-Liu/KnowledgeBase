"""Verify retained comparisons, historical input identity, and local report links."""
import json
from pathlib import Path
import re
from evals import judge
from evals.evaluate import digest,read_jsonl,timestamp,write_json
DIR=Path(__file__).parent
BASE=DIR.parent/'20260925T002400Z-semantic-acceptance'
if __name__=='__main__':
    checks=[]
    run=json.loads((DIR/'run.json').read_text())
    assert run['status']=='completed'
    for name,checksum in run['baseline_sha256'].items():assert digest((BASE/name).read_bytes())==checksum
    checks.append('Original input artifacts unchanged.')
    assert judge.protocol_hash()==json.loads((DIR.parent/'20260925-generation-citations/freeze.json').read_text())['judge_protocol_sha256']
    checks.append('Frozen v11 protocol unchanged.')
    origins={}
    for strategy in ('parent_child','semantic'):
        for unit in ('child','parent'):
            for budget in (4096,6144):
                rows=read_jsonl(DIR/f'{strategy}-{unit}-{budget}.jsonl')
                assert len(rows)==24 and all(r['status']=='ok' for r in rows)
                for r in rows:
                    assert r['retrieval']['evidence_tokens']<=budget
                    assert r['retrieval']['rerank']['model_revision']==run['model_revision']
                    origins[r['scores_origin']]=origins.get(r['scores_origin'],0)+1
    assert origins=={'historical':96,'local-inference':48,'same-run-cache':48}
    checks.append('192 successful replay rows preserve bounded evidence and model identity; exactly 48 fresh local scoring queries.')
    comparison=json.loads((DIR/'comparison.json').read_text())
    changed=comparison['semantic-parent-6144']['case_changes']
    assert {r['case_id'] for r in changed}=={'msds-working-enrollment','msds-cpt-source-context'}
    assert all(r['before']['annotated_char_recall']==.5 and r['after']['annotated_char_recall']==1 for r in changed)
    checks.append('Exactly the two documented coverage improvements; no hidden span-coverage regressions.')
    genrun=json.loads((DIR/'generation-run.json').read_text())
    for label,checksum in genrun['inputs_sha256'].items():assert digest((DIR/f'{label}.jsonl').read_bytes())==checksum
    answers=read_jsonl(DIR/'generation-answers.jsonl');calls=read_jsonl(DIR/'generation-calls.jsonl')
    assert len(answers)==len(calls)==4 and all(r['status']=='ok' for r in answers+calls)
    checks.append('Four completed generation-only requests, exact frozen retrieval inputs, all attempts retained.')
    for review in json.loads((DIR/'manual-review.json').read_text()):
        row=next(r for r in answers if (r['case_id'],r['variant'])==(review['case_id'],review['variant']))
        assert digest(row['answer'].encode())==review['answer_sha256']
        for point in review['points']:
            assert point['answer_quote'] in row['answer']
            for e in point['evidence']:
                source=next(s for s in row['sources'] if s['source_id']==e['source_id'])
                assert source['text'][e['start_offset']-source['start_offset']:e['end_offset']-source['start_offset']]==e['quote']
    checks.append('Manual review answer/evidence quotes match raw bytes and source offsets.')
    docs=[Path(p) for p in ('README.md','docs/configuration.md','docs/answer-grounding.md','docs/reranking.md','docs/parent-reranking.md','docs/v1/README.md','docs/v1/merge-readiness.md',
        'evals/library-runs/20260925-parent-reranking/README.md','evals/library-runs/20260925-parent-reranking/PLAN.md','evals/library-runs/20260925-review-supplement-3/README.md','evals/check-runs/20260925-retrieval-coverage/README.md')]
    link_count=0
    for path in docs:
        content=path.read_text();assert content.count('```')%2==0
        for target in re.findall(r'\]\(([^)]+)\)',content):
            if '://' in target or target.startswith('#'):continue
            assert (path.parent/target.split('#')[0]).exists(),(path,target)
            link_count+=1
    checks.append(f'Reviewed English content, balanced fences and {link_count} local Markdown link targets in changed reports/docs.')
    for directory in [DIR,DIR.parent/'20260925-review-supplement',DIR.parent/'20260925-review-supplement-2',DIR.parent/'20260925-review-supplement-3',DIR.parent/'20260925-retrieval-diagnostic']:
        for path in directory.rglob('*'):
            if path.is_file() and path.suffix in {'.json','.jsonl','.md','.py','.log'}:
                assert not re.search(r'\bsk-[A-Za-z0-9_-]{24,}',path.read_text()),path
    checks.append('No API-key-shaped secrets found in new textual artifacts.')
    write_json(DIR/'final-audit.json',{'timestamp':timestamp(),'passed':len(checks),'checks':checks,'scope':'Artifact integrity and documentation review; not a new quality benchmark.'})
    print(len(checks),'passed')
