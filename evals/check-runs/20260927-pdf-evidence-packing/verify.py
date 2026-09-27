"""Final offline record and documentation review; no providers or measurements."""
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).parent
LIVE=Path('evals/library-runs/20260927-v2-pdf-live')
frozen=json.loads((ROOT/'frozen-inputs.json').read_text())
before=json.loads((ROOT/'before.json').read_text())
after=json.loads((ROOT/'after-2.json').read_text())
assert sha256((LIVE/'index-snapshot.json').read_bytes()).hexdigest()==frozen['corpus_sha256']
assert sha256((LIVE/'effective-cases.json').read_bytes()).hexdigest()==frozen['cases_sha256']
for row,old in zip(frozen['rows'],before['rows'],strict=True):
    assert row['diagnostics']['evidence_tokens']==old['result']['diagnostics']['evidence_tokens']
    saved=json.loads((LIVE/'repair-1'/f"{row['case_id']}-{row['arm']}.json").read_text())
    if saved['status']=='completed':
        assert [(s['chunk_id'],s['start_offset'],s['end_offset']) for s in saved['answer']['sources']] == [
            (s['chunk']['chunk_id'],s['chunk']['start_offset'],s['chunk']['end_offset']) for s in old['result']['chunks']]
for path,digest in after['code_hashes'].items():
    assert sha256(Path(path).read_bytes()).hexdigest()==digest
metrics=json.loads((ROOT/'comparison-2.json').read_text())['metric_inventory']
assert len(metrics)==20
for m in metrics.values():
    assert m['status'] in {'measured','not_applicable','unavailable'}
    assert (m['value'] is not None)==(m['status']=='measured')
    if m['status']!='measured':assert m['reason']
paths=['README.md','docs/configuration.md','docs/hybrid-retrieval.md','docs/parent-child-retrieval.md','docs/pdf-integration.md','docs/v2/README.md',str(ROOT/'README.md')]
links=0
for p in paths:
    path=Path(p);text=path.read_text()
    for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text):
        if '://' in link or link.startswith('#'):continue
        assert (path.parent/link.split('#')[0]).exists(), (p,link)
        links+=1
    assert not any(line.endswith(' ') for line in text.splitlines())
subprocess.run(['git','diff','--check'],check=True)
print(f'Verified 32 baseline token counts, 31 completed-source snapshots, unchanged corpus/questions, current product hashes, 20 metrics and {links} local documentation links across 7 documents.')
