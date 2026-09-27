"""Review the prepared harness without importing servers or calling providers."""
import ast
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

from clone_index import DATA, SOURCE, database_tables, manifest

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT.parent / '20260927-dense-table-acceptance'
for script in ROOT.glob('*.py'):
    ast.parse(script.read_text(), filename=str(script))
    print(f'Syntax reviewed: {script.name}')
for copied, original in [
    ('frozen-cases.json', 'frozen-cases.json'),
    ('frozen-original-protocol.md', 'protocol.md'),
    ('frozen-fact-labels.json', 'metrics/fact-labels.json'),
    ('baseline-index-snapshot.json', 'index-snapshot.json'),
]:
    assert (ROOT / copied).read_bytes() == (BASELINE / original).read_bytes()
assert (ROOT / 'frozen-gold.json').read_bytes() == Path('evals/check-runs/20260927-dense-table/gold.json').read_bytes()
cases = json.loads((ROOT / 'frozen-cases.json').read_text())['cases']
assert len(cases) == 3 and all(case['followup_of'] is None for case in cases)
for name in ['protocol.md', 'frozen-original-protocol.md']:
    text = (ROOT / name).read_text()
    for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)', text):
        assert ((ROOT / link.split('#', 1)[0]).resolve()).is_file(), f'Missing {name} link: {link}'
    assert not re.search(r'[\u4e00-\u9fff]', text)
    assert text.count('\n```') % 2 == 0
reuse = json.loads((ROOT / 'index-reuse.json').read_text())
assert manifest(SOURCE) == reuse['source_file_hashes'] == manifest(DATA)
assert database_tables(SOURCE) == database_tables(DATA)
assert reuse['provider_calls'] == 0
assert not any((ROOT / name).exists() for name in ['server-start.json', 'resolved-runtime.json', 'server-observations.jsonl'])
subprocess.run(['git','diff','--check','--',str(ROOT)],check=True)
print('Review: exact frozen questions, rubric, gold, label binding and baseline snapshot preserved; copied index and all history rows unchanged; valid local links and English prose; server not started and no provider calls made.')
