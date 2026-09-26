"""Retain the final content, link and formatting audit without provider calls."""
import json
from pathlib import Path
import re
import subprocess
from time import perf_counter
from evals.evaluate import digest, git_state, timestamp, write_json
DIR=Path(__file__).parent
FILES=[Path(p) for p in ['README.md','docs/v1/README.md','docs/v1/merge-readiness.md',
    'docs/answer-grounding.md','docs/document-scope.md',str(DIR/'README.md'),
    'evals/library-runs/20260926-comparison-awake/README.md',
    'evals/library-runs/20260926-comparison-awake/REVIEW.md',
    'evals/library-runs/20260926-comparison-awake/METRICS.md']]
if __name__=='__main__':
    target=DIR/'doc-review-1.json'
    assert not target.exists()
    start,started_at=perf_counter(),timestamp();errors=[];links=[]
    for path in FILES:
        text=path.read_text()
        if re.search(r'[\u3400-\u9fff]',text):errors.append(f'{path}: non-English CJK text')
        if sum(line.startswith('```') for line in text.splitlines())%2:errors.append(f'{path}: unbalanced code fence')
        for ref in re.findall(r'\[[^\]]*\]\(([^)]+)\)',text):
            if '://' in ref or ref.startswith('#'):continue
            exists=(path.parent/ref.split('#')[0]).exists()
            links.append({'file':str(path),'target':ref,'exists':exists})
            if not exists:errors.append(f'{path}: missing {ref}')
    diff=subprocess.run(['git','diff','--check'],capture_output=True,text=True)
    if diff.returncode:errors.append(diff.stdout+diff.stderr)
    inventory=json.loads((DIR/'artifact-audit-1.json').read_text())['metric_inventory']
    for key in inventory:inventory[key]={'status':'not_applicable','value':None,'reason':'Documentation content/link/format review, no provider or runtime workload.'}
    write_json(target,{'command':['uv','run','python','-m','evals.check-runs.20260926-generation-diagnostics.review_docs'],
        'started_at':started_at,'finished_at':timestamp(),'seconds':perf_counter()-start,'git':git_state(),
        'status':'passed' if not errors else 'failed','reviewer':'Codex implementer',
        'content_review':['11/11 strict and service cases supported by fixed references and source review; no new criteria.',
            'Active/wall latency values and sample counts checked against metrics.json.',
            'Sleep correlation is evidence of confounding, not proof of sole causation.',
            'Raw warning remains visible, scoped non-reproduction does not establish no resource leaks.',
            'Historical failures unchanged; no independent human, held-out, live UI or load-capacity claim.',
            'Merge recommendation separated from explicit authorization.'],
        'files':{str(p):digest(p.read_bytes()) for p in FILES},'local_links':links,'errors':errors,'metric_inventory':inventory})
    print(f'{len(FILES)} documents, {len(links)} local links, {len(errors)} errors.')
    for error in errors:print(error)
    raise SystemExit(bool(errors))
