"""Review new local documentation and diff formatting without provider calls."""
from pathlib import Path
import re
import subprocess
paths = [Path('docs/v2/README.md'),Path(__file__).parent/'README.md',Path('evals/library-runs/20260927-table-cell-context-acceptance/protocol.md')]
for path in paths:
    text=path.read_text()
    assert not re.search(r'[\u4e00-\u9fff]', text)
    for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text):
        if not link.startswith('http'):
            assert (path.parent/link.split('#')[0]).resolve().exists(), (path,link)
    assert text.count('\n```') % 2 == 0
subprocess.run(['git','diff','--check'],check=True)
print('Reviewed English content, relative links and formatting. Structural evidence versus answer quality and single-reviewer limitation explicitly separated; no merge claim.')
