"""Check acceptance artifacts and links without another live model call."""
from hashlib import sha256
import json,re,socket,subprocess
from pathlib import Path
from knowledgebase.config import Settings
from prepare import ROOT, MATERIAL
read=lambda n:json.loads((ROOT/n).read_text())
freeze=json.loads((MATERIAL/'freeze.json').read_text())
for group in ['input_hashes','product_hashes']:
    assert all(sha256(Path(p).read_bytes()).hexdigest()==v for p,v in freeze[group].items())
assert subprocess.check_output(['git','branch','--show-current'],text=True).strip()=='v2'
print('1 passed: sealed input and product files unchanged; active branch v2.')
labels=read('frozen-labels.json');snapshot=read('index-snapshot.json')
assert len(labels)==12 and all(x['fully_mapped'] for x in labels.values())
for label in labels.values():
    for match in label['canonical_matches']:
        doc=next(d for d in snapshot['files'] if d['file']['file_id']==match['file_id'])
        block=next(b for b in doc['extraction']['blocks'] if b['source_ref']==match['source_ref'])
        assert block['text'][match['start']-block['start_offset']:match['end']-block['start_offset']]==match['text']
        assert any(r['page_index']+1==label['physical_page'] for r in block['regions'])
assert read('execution-freeze.json')['answer_calls']==0
print('1 passed: twelve exact mapped references match indexed page/span provenance and pre-answer freeze.')
questions=json.loads((MATERIAL/'questions.json').read_text())['questions'];answers=[]
for q in questions:
    row=read(q['id']+'-planned.json');answers.append(row)
    assert row['request']['question']==q['question']
    assert set(row['request'])=={'question','file_ids','request_id','retrieval_mode'}
    assert set(row['request']['file_ids'])=={d['file']['file_id'] for d in snapshot['files'] if d['file']['file_name'] in q['files']}
assert [x['status'] for x in answers]==['completed','completed','error','completed','completed','completed']
assert sum(x.get('history_matches',False) for x in answers)==5
assert read('review.json')['summary']['case_gate']['passed']==4
assert read('review.json')['summary']['correctness']=={'correct':7,'expected':13}
assert sum(len(x['claims']) for x in read('review.json')['cases'])==7
print('1 passed: all six frozen requests retained in scope; error, refusal and exact claim denominators visible.')
from record_check import METRICS
assert set(read('measurement.json')['metric_inventory'])==set(METRICS)
assert read('diagnostics.json')['summary']['sdk_starts']==28
assert read('diagnostics.json')['summary']['sdk_terminals']==28
assert read('dependency-review.json')['status']=='not_exercised'
assert read('failure-reproduction.json')['restricted']['scope_preserved']
assert read('server-stop.json')['database_row_counts']['chroma/chroma.sqlite3']['embeddings']==566
assert read('server-stop.json')['port_closed']
with socket.socket() as s:assert s.connect_ex(('127.0.0.1',8787))!=0
print('1 passed: all twenty metrics, local failure reproduction, dependency limit and closed server recorded.')
for name in ['browser-result.json','browser-result-2.json','browser-navigation-result.json']:
    b=read(name);assert b['no_extra_provider_calls']
review=read('browser-review.json');assert len(review['checks'])==12 and not review['full_protocol_passed']
assert all((ROOT/p).exists() for p in review['images_inspected'])
for p in ROOT.glob('*.har'):
    assert all(e['request']['method']=='GET' for e in json.loads(p.read_text())['log']['entries'])
print('1 passed: browser evidence retained at both widths; blocked/partial checks remain; no new answer calls.')
for p in [ROOT/'README.md',Path('docs/v2/README.md')]:
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
        if '://' in target or target.startswith('#'):continue
        assert (p.parent/target.split('#')[0]).exists(),(p,target)
    assert not re.search(r'[\u4e00-\u9fff]',p.read_text())
    assert all(line.rstrip()==line for line in p.read_text().splitlines())
print('1 passed: authored documentation links, English text and formatting reviewed.')
secret=Settings().openai_api_key.encode()
for p in ROOT.iterdir():
    if p.is_file():assert secret not in p.read_bytes(),f'Credential found in {p.name}'
print('1 passed: no configured credential in retained artifacts.')
