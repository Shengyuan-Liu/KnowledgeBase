"""Keep independent Poppler page text for reference annotation, not product scoring."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from acquire import MATERIALS, ROOT

manifest = json.loads((MATERIALS / 'manifest.json').read_text())
records = []
for entry in manifest['files']:
    raw = subprocess.check_output(['pdftotext', str(MATERIALS / entry['file']), '-']).decode()
    pages = raw.split('\f')
    assert not pages[-1].strip()
    pages.pop()
    assert len(pages) == entry['physical_pages']
    records.append(dict(file=entry['file'], source_sha256=entry['sha256'], pages=[
        dict(physical_page=i+1, text=text) for i, text in enumerate(pages)]))
with (ROOT / 'reference-reading-text.json').open('x') as output:
    json.dump(dict(tool=subprocess.check_output(['pdftotext', '-v'], stderr=subprocess.STDOUT, text=True).splitlines()[0],
        method='Poppler reading-order text for finding candidate prose/table evidence. Original-page visual review defines truth. This is not the product Docling extraction or retrieval labels.',
        manifest_sha256=sha256((MATERIALS/'manifest.json').read_bytes()).hexdigest(), documents=records), output, indent=2)
    output.write('\n')
print('Independent text retained for all 90 physical pages; no product ingestion or model call.')
