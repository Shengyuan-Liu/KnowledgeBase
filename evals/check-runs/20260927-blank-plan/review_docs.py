"""Review edited source/docs while preserving whitespace in raw table evidence."""
from pathlib import Path
import re
import subprocess
paths=[Path('docs/v2/README.md'),Path('docs/planned-retrieval.md'),Path('docs/dependent-retrieval.md'),Path(__file__).parent/'README.md',Path('evals/library-runs/20260927-blank-plan-acceptance/protocol.md')]
links=0
for path in paths:
    text=path.read_text()
    assert not re.search(r'[\u4e00-\u9fff]',text)
    assert text.count('\n```')%2==0
    for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text):
        if not link.startswith('http'):
            assert (path.parent/link.split('#',1)[0]).resolve().exists(),(path,link)
            links+=1
subprocess.run(['git','diff','--check','--','knowledgebase','tests','docs'],check=True)
print(f'Reviewed {len(paths)} English documents and {links} local links; raw source cells unchanged, bounded coverage query disclosed, no live quality or merge claim.')
