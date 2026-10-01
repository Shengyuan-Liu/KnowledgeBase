"""Freeze new original PDFs before authoring any reference questions."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parent
MATERIALS = ROOT.parents[1] / 'materials/pdf-v2-candidate-20261001'
SOURCES = [
    ('rag-paper.pdf', 'paper', 'Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks',
     'https://papers.nips.cc/paper/2020/file/6b493230205f780e1bc26945df7481e5-Paper.pdf',
     'https://papers.nips.cc/paper_files/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html',
     'Original authors/publisher retain rights; public conference paper retained as a local evaluation fixture.'),
    ('dpr-paper.pdf', 'paper', 'Dense Passage Retrieval for Open-Domain Question Answering',
     'https://aclanthology.org/2020.emnlp-main.550.pdf',
     'https://aclanthology.org/2020.emnlp-main.550/',
     'Copyright 2020 Association for Computational Linguistics; original notice retained.'),
    ('decision-trees.pdf', 'lecture', 'Decision Trees - Andrew W. Moore',
     'https://www.cs.cmu.edu/afs/cs/Web/People/awm/tutorials/dtree18.pdf',
     'https://www.cs.cmu.edu/afs/cs/Web/People/awm/tutorials/dtree.html',
     'Copyright Andrew W. Moore; original educational-use notice and source attribution retained. No relicensing is claimed.'),
    ('nvidia-fy25.pdf', 'company_report', 'CFO Commentary on Fourth Quarter and Fiscal 2025 Results',
     'https://investor.nvidia.com/files/doc_financials/2025/Q425/Q4FY25-CFO-Commentary.pdf',
     'https://investor.nvidia.com/news/press-release-details/2025/NVIDIA-Announces-Financial-Results-for-Fourth-Quarter-and-Fiscal-2025/default.aspx',
     'Copyright 2025 NVIDIA Corporation. All rights reserved; public investor document retained as a local evaluation fixture.'),
]


def main():
    assert not (MATERIALS / 'cases.json').exists()
    files, attempts = [], []
    for name, category, title, url, landing, rights in SOURCES:
        with urllib.request.urlopen(url, timeout=60) as response:
            content = response.read()
            attempt = dict(file=name, requested_url=url, final_url=response.url,
                           status=response.status, content_type=response.headers.get('Content-Type'),
                           retrieved_at=datetime.now(timezone.utc).isoformat())
        attempts.append(attempt)
        assert content.startswith(b'%PDF-'), name
        path = MATERIALS / name
        with path.open('xb') as output:
            output.write(content)
        info = subprocess.check_output(['pdfinfo', str(path)], text=True)
        pages = int(next(line for line in info.splitlines() if line.startswith('Pages:')).split()[1])
        files.append(dict(file=name, category=category, title=title, source_url=url,
                          landing_url=landing, sha256=sha256(content).hexdigest(), bytes=len(content),
                          physical_pages=pages, rights=rights, acquisition=attempt))
        print(name, pages, 'pages;', len(content), 'bytes')
    old = json.loads((MATERIALS.parent / 'pdf-v2/manifest.json').read_text())
    assert not {f['sha256'] for f in files} & {f['sha256'] for f in old}
    with (MATERIALS / 'manifest.json').open('x') as output:
        json.dump(dict(frozen_at=datetime.now(timezone.utc).isoformat(), files=files,
                       relation_to_prior_corpus='No byte-identical PDF from the prior five-file development corpus. Public papers may be familiar to pretrained models; this is not proof of model-training independence.'), output, indent=2)
        output.write('\n')
    with (ROOT / 'acquisition.json').open('x') as output:
        json.dump(attempts, output, indent=2)
        output.write('\n')


if __name__ == '__main__':
    main()
