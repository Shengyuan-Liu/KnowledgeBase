"""Retain the first download attempt and freeze the replacement official report."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import urllib.request
from acquire import MATERIALS, ROOT, SOURCES

URL = 'https://nvidianews.nvidia.com/_gallery/download_pdf/67bf85d73d633281c6875f57/'


def main():
    with urllib.request.urlopen(URL, timeout=60) as response:
        content = response.read()
        acquisition = dict(file='nvidia-fy25.pdf', requested_url=URL, final_url=response.url,
                           status=response.status, content_type=response.headers.get('Content-Type'),
                           retrieved_at=datetime.now(timezone.utc).isoformat())
    assert content.startswith(b'%PDF-')
    with (MATERIALS / 'nvidia-fy25.pdf').open('xb') as output:
        output.write(content)
    files = []
    for name, category, title, url, landing, rights in SOURCES:
        path = MATERIALS / name
        info = subprocess.check_output(['pdfinfo', str(path)], text=True)
        pages = int(next(line for line in info.splitlines() if line.startswith('Pages:')).split()[1])
        files.append(dict(file=name, category=category,
            title=title if name != 'nvidia-fy25.pdf' else 'NVIDIA Announces Financial Results for Fourth Quarter and Fiscal 2025',
            source_url=url if name != 'nvidia-fy25.pdf' else URL, landing_url=landing,
            sha256=sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size,
            physical_pages=pages, rights=rights,
            acquisition=acquisition if name == 'nvidia-fy25.pdf' else dict(
                attempt='acquisition-1.json', outcome='Downloaded before later report HTTP 403.',
                exact_response_headers='unavailable: first script stopped before writing its metadata list',
                file_mtime_utc=datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat())))
    old = json.loads((MATERIALS.parent / 'pdf-v2/manifest.json').read_text())
    assert not {f['sha256'] for f in files} & {f['sha256'] for f in old}
    with (MATERIALS / 'manifest.json').open('x') as output:
        json.dump(dict(frozen_at=datetime.now(timezone.utc).isoformat(), files=files,
            relation_to_prior_corpus='All four files are new to project evaluation; public material may be familiar to pretrained models. No independent human or model-training holdout claim.',
            acquisition_limit='The CFO commentary returned HTTP 403. The publicly linked official NVIDIA press-release PDF was selected instead, before writing questions. Failed attempt is retained; no credential or access-control bypass.'), output, indent=2)
        output.write('\n')
    print('Frozen four original PDFs before questions:', sum(f['physical_pages'] for f in files), 'physical pages.')


if __name__ == '__main__':
    main()
