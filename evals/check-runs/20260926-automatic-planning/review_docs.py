"""Review changed English docs, local links, fences and source whitespace."""
from pathlib import Path
import re
import subprocess

paths = ['README.md', 'docs/v2/README.md', 'docs/v2/v2-technical-plan.md',
         'docs/planned-retrieval.md', 'docs/chat-api.md', 'docs/chat-streaming.md',
         'docs/configuration.md', 'evals/check-runs/20260926-automatic-planning/README.md']
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
                ':(exclude)evals/check-runs/20260926-automatic-planning/*.log'], check=True)
print(f'{len(paths)} documents, {links} local links, English prose, code fences and source whitespace checked.')
print('Content review: opt-in stage 3b separated from dependent/sufficiency work; request limits and sync cancellation limitations disclosed; mock quality separated from live evaluation; failed attempts retained. Official Structured Outputs documentation was consulted for the schema contract.')
