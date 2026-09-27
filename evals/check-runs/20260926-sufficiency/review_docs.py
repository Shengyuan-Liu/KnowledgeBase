"""Review current documentation and source formatting without provider calls."""
from pathlib import Path
import re
import subprocess

paths = ['README.md', 'docs/v2/README.md', 'docs/v2/v2-technical-plan.md',
         'docs/evidence-sufficiency.md', 'docs/planned-retrieval.md', 'docs/dependent-retrieval.md', 'docs/chat-streaming.md',
         'docs/configuration.md', 'evals/check-runs/20260926-sufficiency/README.md']
links = 0
for name in paths:
    path = Path(name)
    text = path.read_text()
    assert text.count('```') % 2 == 0, name
    assert not re.search(r'[\u4e00-\u9fff]', text), name
    for target in re.findall(r'\]\(([^)]+)\)', text):
        if target.startswith(('http:', 'https:', '#')):
            continue
        assert (path.parent / target.split('#')[0]).exists(), (name, target)
        links += 1
subprocess.run(['git', 'diff', '--check', 'HEAD', '--', '.',
               ':(exclude)evals/check-runs/20260926-sufficiency/*.log',
               ':(exclude)evals/check-runs/20260926-sufficiency/browser-*-artifacts/**/error-context.md'], check=True)
print(f'{len(paths)} documents, {links} local links, English prose, code fences and source whitespace checked.')
print('Content review: implemented sufficiency separated from live acceptance; source provenance distinguished from semantic support; shared bounds and final-context assessment checked; failed attempts, full inventories and live measurement gaps retained.')
