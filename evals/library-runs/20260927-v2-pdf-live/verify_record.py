"""Verify retained records, source identity, credential exclusion and local links."""
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

from dotenv import dotenv_values

ROOT = Path(__file__).parent
repo = Path.cwd()
metrics = json.loads((ROOT/'measurement-v2.json').read_text())
cases = json.loads((ROOT/'effective-cases.json').read_text())
review = json.loads((ROOT/'reviewed-cases.json').read_text())['rows']
assert len(review) == 64
for folder in [ROOT,ROOT/'repair-1']:
    runtime = json.loads((folder/'resolved-runtime.json').read_text())
    for file in cases['corpus']:
        assert sha256((repo/'evals/materials/pdf-v2'/file['file']).read_bytes()).hexdigest() == file['sha256']
    for case in cases['cases']:
        for arm in ['single','planned']:
            row=json.loads((folder/f"{case['id']}-{arm}.json").read_text())
            if row['status']=='completed':
                assert row['history_matches'] and row['history_retrieval_matches']
                allowed=set(row['request']['file_ids'])
                assert {s['file_id'] for s in row['answer']['sources']} <= allowed
                assert row['answer']['retrieval']['evidence_tokens'] <= 4096
    if folder.name=='repair-1':
        assert all(sha256(Path(p).read_bytes()).hexdigest()==h for p,h in runtime['source_hashes'].items())
for group in metrics['groups'].values():
    assert len(group)==20
    for m in group.values():
        assert m['status'] in ['measured','unavailable','not_applicable']
        if m['status']=='measured':
            assert m['value'] is not None
        else:
            assert m['value'] is None and m['reason']
for row in review:
    artifact=ROOT/row['source_artifact']
    actual=json.loads(artifact.read_text()).get('answer',{}).get('answer','')
    for claim in row['factual_claim_groups']:
        assert claim['text'] in actual
        assert claim['context_support'] in [0,.5,1]
        if claim['citation_support'] is None:
            assert not claim['cited_source_ids']
# Check only for the configured credential; never print or persist its value.
key=dotenv_values('.env').get('OPENAI_API_KEY')
assert key
for path in ROOT.rglob('*'):
    if path.is_file() and '__pycache__' not in path.parts:
        assert key.encode() not in path.read_bytes(), f'Credential present in {path}'
changed_docs=[repo/p for p in ['docs/evidence-sufficiency.md','docs/pdf-integration.md','docs/planned-retrieval.md','docs/v2/README.md','docs/v2/v2-evaluation-plan.md']]
for doc in [*changed_docs,*ROOT.rglob('*.md')]:
    text=doc.read_text()
    for label,target in re.findall(r'\[([^\]]+)\]\(([^)]+)\)',text):
        if '://' in target or target.startswith('#'):
            continue
        target=unquote(target.split('#')[0])
        assert (doc.parent/target).exists(), f'Broken link: {doc}: {target}'
    assert not any(line.endswith(' ') for line in text.splitlines()), f'Trailing whitespace: {doc}'
subprocess.run(['git','diff','--check'],check=True)
print('Verified 64 retained turns, 5 original hashes, 56 history snapshots, scope/budget limits, 20-metric inventories, current repair source hashes, exact reviewed claims, credential exclusion, documentation links and formatting.')
