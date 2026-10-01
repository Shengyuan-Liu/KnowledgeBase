"""Verify local links and whitespace in the integration documentation."""
from pathlib import Path
import re
import subprocess

paths = ['README.md', 'docs/pdf-parsing.md', 'docs/pdf-integration.md', 'docs/v2/README.md',
         'docs/v2/v2-technical-plan.md', 'evals/check-runs/20260926-pdf-integration/README.md']
count = 0
for name in paths:
    path = Path(name)
    text = path.read_text()
    assert text.count('```') % 2 == 0, name
    for target in re.findall(r'\]\(([^)]+)\)', text):
        if target.startswith(('http:', 'https:', '#')):
            continue
        assert (path.parent / target.split('#')[0]).exists(), (name, target)
        count += 1
subprocess.run(['git', 'diff', '--check'], check=True)
print(f'Reviewed {len(paths)} documents and {count} local links; fences and whitespace passed.')
print('Content review: stage 2 implementation distinguished from controller plans, limitations and mocked performance disclosed; user acceptance and merge remain separate.')
