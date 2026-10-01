"""Retain the previous-page heading for the continued financial table."""
from hashlib import sha256
import json
import subprocess
from acquire import MATERIALS, ROOT

prefix = ROOT / 'source-review/nvidia-fy25-page-7'
subprocess.run(['pdftoppm', '-f', '7', '-l', '7', '-scale-to', '1800', '-singlefile',
                '-png', str(MATERIALS/'nvidia-fy25.pdf'), str(prefix)], check=True)
path = prefix.with_suffix('.png')
with (ROOT / 'header-render.json').open('x') as output:
    json.dump(dict(file='nvidia-fy25.pdf', physical_page=7, render=str(path.relative_to(ROOT)),
                   sha256=sha256(path.read_bytes()).hexdigest()), output, indent=2)
    output.write('\n')
print('Retained page 7 headings for the table continued on page 8.')
