"""Seal the reference package before production ingestion or model execution."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from acquire import MATERIALS, ROOT

assert not subprocess.check_output(['git', 'diff', 'HEAD', '--', 'knowledgebase', 'frontend/src'], text=True)
inputs = [*MATERIALS.glob('*.pdf'), *MATERIALS.glob('*.json'), *MATERIALS.glob('*.md'),
          ROOT/'reference-page-text.json', ROOT/'reference-reading-text.json', ROOT/'absence-review.json',
          ROOT/'render-manifest.json', ROOT/'header-render.json', *ROOT.glob('source-review/*.png')]
product_paths = subprocess.check_output(['git', 'ls-files', 'knowledgebase', 'frontend/src'], text=True).splitlines()
record = dict(
    sealed_at=datetime.now(timezone.utc).isoformat(),
    code_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    state='Prepared before production ingestion, canonical span mapping, live answers or browser execution.',
    input_hashes={str(p.relative_to(Path.cwd())): sha256(p.read_bytes()).hexdigest() for p in sorted(inputs)},
    product_hashes={p: sha256(Path(p).read_bytes()).hexdigest() for p in product_paths},
    reviewer='Codex (model)', independent_human_review=False,
    visual_review=dict(physical_pages=8, scope='All retained original-page renders viewed; statements and period/group/unit associations manually compared by Codex.'),
    provider_calls_in_preparation=0,
    future_settings='Freeze exact resolved runtime again immediately before execution; current package does not imply future settings were observed.',
)
with (MATERIALS/'freeze.json').open('x') as output:
    json.dump(record, output, indent=2)
    output.write('\n')
print('Sealed original bytes, references, protocols, render evidence and current product hashes.')
