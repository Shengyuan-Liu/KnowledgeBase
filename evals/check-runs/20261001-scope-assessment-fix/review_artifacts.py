"""Review authored documentation, replay provenance and recorded test scope."""
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parent
for path in [ROOT/'README.md',Path('docs/v2/README.md')]:
    text=path.read_text()
    assert not re.search(r'[\u4e00-\u9fff]',text)
    assert all(line.rstrip()==line for line in text.splitlines())
    for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',text):
        if '://' not in link and not link.startswith('#'):
            assert (path.parent/link.split('#')[0]).exists(),(path,link)
print('1 passed: English documentation, local links and formatting reviewed.')
fixture=json.loads(Path('tests/fixtures/new_pdf_scope_failures.json').read_text())
assert all(sha256(Path(p).read_bytes()).hexdigest()==digest for p,digest in fixture['provenance'].items())
comparison=json.loads((ROOT/'comparison.json').read_text())
assert all(sha256(Path(p).read_bytes()).hexdigest()==digest for p,digest in comparison['current_source_hashes'].items())
assert comparison['summary']['financial_scopes_resolved_after']==4
assert comparison['summary']['unchanged_successful_assessments']==4
assert comparison['provider_calls']==0
print('1 passed: baseline evidence unchanged; replay matches delivered production sources.')
from record_check import METRICS
for name in ['regressions-before','scoped-tests','recorded-replay','scoped-tests-final']:
    record=json.loads((ROOT/(name+'.json')).read_text())
    assert set(record['metric_inventory'])==set(METRICS)
    assert all(m['status']=='not_applicable' for m in record['metric_inventory'].values())
    assert (ROOT/record['failures_artifact']).exists()
assert json.loads((ROOT/'scoped-tests-final.json').read_text())['counts']['passed']==185
assert json.loads((ROOT/'scoped-tests-final.json').read_text())['exit_code']==0
assert subprocess.check_output(['git','branch','--show-current'],text=True).strip()=='v2'
print('1 passed: all command records retain twenty metrics, failures and final 185-test success on v2.')
