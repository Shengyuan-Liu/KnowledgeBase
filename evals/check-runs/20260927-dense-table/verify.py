"""Review retained evidence, dependency scope, documentation links and formatting."""
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import tomllib

from record_check import METRICS

DIRECTORY = Path(__file__).resolve().parent
ROOT = DIRECTORY.parents[2]
comparison = json.loads((DIRECTORY / 'comparison-1/run.json').read_text())
assert comparison['status'] == 'success'
for key in ['inputs', 'implementation']:
    for name, digest in comparison[key].items():
        assert sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
for case in comparison['cases']:
    assert sha256((ROOT / case['frozen_docling']).read_bytes()).hexdigest() == case['frozen_docling_sha256']
    assert case['source_hash_unchanged']
    if case['case'] != 'background-checks':
        assert case['canonical_text_unchanged'] and case['blocks_unchanged'] and not case['recovered_tables']
    else:
        assert all(n == d for n, d in case['after_scores'].values())
        assert all(n == 0 for n, d in case['before_scores'].values())
for name, count in [('focused-tests-1', 54), ('backend-tests-1', 764)]:
    result = json.loads((DIRECTORY / f'{name}.json').read_text())
    assert result['exit_code'] == 0 and result['counts']['passed'] == count
    assert result['counts']['failed'] == result['counts']['error'] == 0
assert json.loads((DIRECTORY / 'backend-tests-1.json').read_text())['counts']['skipped'] == 1
for name in ['dependency-lock-check-1', 'comparison-1', 'environment-restore-1']:
    assert json.loads((DIRECTORY / f'{name}.json').read_text())['exit_code'] == 0
assert json.loads((DIRECTORY / 'native-probes/report-review-1.json').read_text())['exit_code'] != 0
assert json.loads((DIRECTORY / 'native-probes/report-review-2.json').read_text())['exit_code'] == 0
inventories = 0
for path in DIRECTORY.rglob('*.json'):
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or 'metric_inventory' not in data:
        continue
    metrics = data['metric_inventory']
    assert set(metrics) == set(METRICS), path
    for metric in metrics.values():
        assert metric['status'] in ['measured', 'not_applicable', 'unavailable'], path
        assert (metric['value'] is not None) == (metric['status'] == 'measured'), path
        if metric['status'] != 'measured':
            assert metric['reason'], path
    inventories += 1
old = tomllib.loads(subprocess.check_output(['git', 'show', 'HEAD:uv.lock'], text=True))
new = tomllib.loads((ROOT / 'uv.lock').read_text())
a = {p['name']: p for p in old['package']}
b = {p['name']: p for p in new['package']}
assert b.keys() - a.keys() == {'pdfplumber', 'pdfminer-six', 'cryptography'}
assert not a.keys() - b.keys()
assert all(a[n] == b[n] for n in a.keys() & b.keys() if n != 'knowledgebase')
removed = set(re.findall(r'^ - (.+)$', (DIRECTORY / 'dependency-sync-1.log').read_text(), re.M))
restored = set(re.findall(r'^ \+ (.+)$', (DIRECTORY / 'environment-restore-1.log').read_text(), re.M))
assert len(removed) == 69 and removed == restored
paths = [ROOT / name for name in ['docs/pdf-parsing.md', 'docs/pdf-integration.md', 'docs/v2/README.md']]
paths += [*DIRECTORY.rglob('README.md'), DIRECTORY / 'protocol.md']
links = 0
for path in paths:
    text = path.read_text()
    for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)', text):
        if '://' in link or link.startswith('#'):
            continue
        assert (path.parent / link.split('#')[0]).exists(), (path, link)
        links += 1
    assert not any(line.endswith(' ') for line in text.splitlines()), path
    assert not re.search(r'[\u4e00-\u9fff]', text), path
subprocess.run(['git', 'diff', '--check'], check=True)
assert subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip() == 'v2'
print(f'Checked {inventories} complete metric inventories, frozen/current hashes, all scoped/full test results, failed attempts, {links} documentation links, English text, formatting, dependency scope and restoration of 69 pre-existing optional packages. No live-provider or general table-fidelity claim.')
