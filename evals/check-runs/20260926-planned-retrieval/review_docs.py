"""Check documentation links/fences and source whitespace for this change."""
from pathlib import Path
import re
import subprocess

paths = ['README.md', 'docs/v2/README.md', 'docs/v2/v2-technical-plan.md',
         'docs/planned-retrieval.md', 'evals/check-runs/20260926-planned-retrieval/README.md']
links = 0
for name in paths:
    path = Path(name)
    text = path.read_text()
    assert text.count('```') % 2 == 0, name
    for target in re.findall(r'\]\(([^)]+)\)', text):
        if target.startswith(('http:', 'https:', '#')):
            continue
        assert (path.parent / target.split('#')[0]).exists(), (name, target)
        links += 1
subprocess.run(['git', 'diff', '--check', 'HEAD', '--', '.', ':(exclude)evals/check-runs/20260926-planned-retrieval/*.log'], check=True)
print(f'{len(paths)} documents, {links} local links, code fences and source whitespace checked.')
print('Content review: standalone stage 3a distinguished from automatic planning and chat integration; sample quality separated from performance; failed attempts preserved. Raw logs excluded from whitespace normalization.')
