"""Render original physical pages for model visual review before reference freeze."""
from hashlib import sha256
import json
import subprocess
from acquire import MATERIALS, ROOT

PAGES = {'rag-paper.pdf': [3], 'dpr-paper.pdf': [3],
         'decision-trees.pdf': [35], 'nvidia-fy25.pdf': [1, 2, 4, 8]}
records = []
for filename, pages in PAGES.items():
    for page in pages:
        prefix = ROOT / 'source-review' / f'{filename[:-4]}-page-{page}'
        subprocess.run(['pdftoppm', '-f', str(page), '-l', str(page), '-scale-to', '1800',
                        '-singlefile', '-png', str(MATERIALS / filename), str(prefix)], check=True)
        path = prefix.with_suffix('.png')
        records.append(dict(file=filename, physical_page=page, render=str(path.relative_to(ROOT)),
                            sha256=sha256(path.read_bytes()).hexdigest()))
with (ROOT / 'render-manifest.json').open('x') as output:
    json.dump(records, output, indent=2)
    output.write('\n')
print('Rendered seven original physical pages; visual review is recorded separately.')
