"""Verify the prepared corpus/reference contract without provider calls."""
from collections import Counter
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

from knowledgebase.rag.scope import document_references, resolve_document_scope
from knowledgebase.schemas import ScopeFile
from acquire import MATERIALS, ROOT


def read(path):
    return json.loads(path.read_text())


def main():
    manifest = read(MATERIALS/'manifest.json')
    requests = read(MATERIALS/'questions.json')
    references = read(MATERIALS/'references.json')
    freeze = read(MATERIALS/'freeze.json')
    assert datetime.fromisoformat(manifest['frozen_at']) < datetime.fromisoformat(requests['created_at']) < datetime.fromisoformat(freeze['sealed_at'])
    assert references['created_at'] == requests['created_at']
    assert len(manifest['files']) == 4 and sum(f['physical_pages'] for f in manifest['files']) == 90
    assert set(f['category'] for f in manifest['files']) == {'paper','lecture','company_report'}
    old_hashes = {f['sha256'] for f in read(MATERIALS.parent/'pdf-v2/manifest.json')}
    for entry in manifest['files']:
        data = (MATERIALS/entry['file']).read_bytes()
        assert sha256(data).hexdigest() == entry['sha256'] and len(data) == entry['bytes']
        assert entry['sha256'] not in old_hashes and data.startswith(b'%PDF-')
    assert read(ROOT/'acquisition-1.json')['exit_code'] != 0
    assert '403' in (ROOT/'acquisition-1.log').read_text()
    assert read(ROOT/'acquisition-2.json')['exit_code'] == 0
    print('Source bytes, three populations, source-before-question chronology and retained failed acquisition verified.')

    questions = {c['id']: c for c in requests['questions']}
    cases = {c['case_id']: c for c in references['cases']}
    facts = {f['id']: f for f in references['facts']}
    assert len(questions) == len(cases) == 6 and questions.keys() == cases.keys()
    assert len(facts) == 12 and sum(len(c['fact_ids']) for c in cases.values()) == 13
    assert Counter(c['answerability'] for c in cases.values()) == {'full':4, 'partial':1, 'none':1}
    assert all(set(q) == {'id','question','files'} for q in questions.values())
    for identity, case in cases.items():
        for fact_id in case['fact_ids']:
            assert {s['file'] for s in facts[fact_id]['evidence']} <= set(questions[identity]['files'])
    catalog = [ScopeFile(file_id=f'fixture-{i}', file_name=f['file'], labels=[]) for i,f in enumerate(manifest['files'])]
    for question in questions.values():
        allowed = [f.file_id for f in catalog if f.file_name in question['files']]
        result = resolve_document_scope(document_references(question['question']), catalog, file_ids=allowed)
        assert result.status == 'resolved' and result.file_ids == allowed
    full, partial = questions['retriever-training-hop'], questions['retriever-training-restricted']
    assert full['question'] == partial['question'] and 'DPR' not in full['question']
    assert set(full['files']) == {'rag-paper.pdf','dpr-paper.pdf'} and partial['files'] == ['rag-paper.pdf']
    assert all({s['file'] for s in facts[f]['evidence']}.isdisjoint(partial['files']) for f in cases['retriever-training-restricted']['gap_ids'])
    assert cases['retriever-training-hop']['dependency']['target'] in facts['retriever_bridge']['evidence'][0]['raw_quote']
    print('Request/gold separation, six answerability contracts and actual document-scope resolution verified.')

    source_text = read(ROOT/'reference-reading-text.json')
    text_pages = {d['file']:{p['physical_page']:p['text'] for p in d['pages']} for d in source_text['documents']}
    renders = read(ROOT/'render-manifest.json') + [read(ROOT/'header-render.json')]
    assert len(renders) == 8
    rendered = {(r['file'],r['physical_page']) for r in renders}
    spans = [s for f in facts.values() for s in f['evidence']] + [cases['forecast-is-not-actual']['tempting_but_not_answer']]
    for span in spans:
        text = text_pages[span['file']][span['physical_page']]
        assert text[span['reference_text_start']:span['reference_text_end']] == span['raw_quote']
        assert ' '.join(span['raw_quote'].split()) == span['normalized_quote']
        assert (span['file'],span['physical_page']) in rendered
    assert facts['overfitting_definition']['evidence'][0]['physical_page'] == 35
    assert facts['overfitting_definition']['printed_label'] == 'Slide 69'
    assert {facts[k]['table']['value'] for k in ['quarter_gaap','quarter_nongaap','annual_gaap','annual_nongaap']} == {'24,034','25,516','81,453','86,789'}
    assert {c['searched_physical_pages'] for c in read(ROOT/'absence-review.json')['cases']} == {16,10}
    for render in renders:
        assert sha256((ROOT/render['render']).read_bytes()).hexdigest() == render['sha256']
    print('Reference spans, physical pages, table labels, absence-review scope and rendered evidence verified.')

    for mapping in ['input_hashes','product_hashes']:
        for name,digest in freeze[mapping].items():
            assert sha256(Path(name).read_bytes()).hexdigest() == digest, name
    assert freeze['provider_calls_in_preparation'] == 0
    assert not subprocess.check_output(['git','diff','HEAD','--','knowledgebase','frontend/src'],text=True)
    assert subprocess.check_output(['git','branch','--show-current'],text=True).strip() == 'v2'
    print('Sealed inputs and unchanged product verified; no live result inferred from preparation.')

    for path in [*MATERIALS.glob('*.md'), ROOT/'README.md', Path('docs/v2/README.md')]:
        text = path.read_text()
        assert not re.search('[\u4e00-\u9fff]',text)
        assert all(line.rstrip() == line for line in text.splitlines())
        assert ')+retains' not in text and ')+include' not in text
        for link in re.findall(r'\]\(([^)]+)\)',text):
            if not re.match(r'https?://',link) and not link.startswith('#'):
                assert (path.parent/link.split('#')[0]).exists(), (path,link)
    print('English documentation, current scope, local links and formatting reviewed.')
    print('5 passed')


if __name__ == '__main__':
    main()
