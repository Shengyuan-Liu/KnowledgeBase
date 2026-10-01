"""Verify the retained live evidence, metric inventory and documentation offline."""
from hashlib import sha256
import json
import os
from pathlib import Path
import py_compile
import re
import subprocess
from urllib.parse import unquote

from dotenv import dotenv_values

from record_check import METRICS

ROOT = Path(__file__).parent
OLD = ROOT.parent / '20260927-v2-pdf-live'
frozen = json.loads((ROOT / 'frozen-cases.json').read_text())
original = json.loads((OLD / 'effective-cases.json').read_text())
assert frozen['cases'] == [c for c in original['cases'] if c['id'] in {'apple-sales', 'apple-income', 'apparent-conflict'}]
assert frozen['facts'] == {k: original['facts'][k] for k in frozen['facts']}
assert frozen['corpus'] == original['corpus']
snapshot = json.loads((OLD / 'index-snapshot.json').read_text())
texts = {d['file']['file_id']: d['extraction']['text'] for d in snapshot['files']}
runtime = json.loads((ROOT / 'resolved-runtime.json').read_text())
for path, digest in runtime['source_hashes'].items():
    assert sha256(Path(path).read_bytes()).hexdigest() == digest
for path, digest in runtime['harness_hashes'].items():
    assert sha256((ROOT / path).read_bytes()).hexdigest() == digest
preparation = json.loads((ROOT / 'preparation.json').read_text())
assert preparation['snapshot_sha256'] == sha256((OLD / 'index-snapshot.json').read_bytes()).hexdigest()
assert preparation['protocol_sha256'] == sha256((ROOT / 'protocol.md').read_bytes()).hexdigest()
assert preparation['vectors_sha256'] == sha256(Path(preparation['vectors_path']).read_bytes()).hexdigest()
for case in frozen['cases']:
    for arm in ['single', 'planned']:
        row = json.loads((ROOT / f"{case['id']}-{arm}.json").read_text())
        assert row['status'] == 'completed' and row['request']['question'] == case['question']
        assert row['history_matches'] and row['history_retrieval_matches']
        assert row['first_answer_delta_seconds'] <= row['complete_response_seconds']
        answer = row['answer']
        assert ''.join(e['data']['delta'] for e in row['events'] if e['data']['event'] == 'answer_delta') == answer['answer']
        assert answer['answer'] == row['saved_message']['content']
        for source in answer['sources']:
            assert source['text'] == texts[source['file_id']][source['start_offset']:source['end_offset']]
            for supplement in source['pdf']['supplements']:
                assert supplement['text'] == texts[source['file_id']][supplement['start_offset']:supplement['end_offset']]
        if arm == 'planned':
            assessment = answer['retrieval']['planning']['assessment']
            assert assessment['record']['prompt_version'] == 'evidence-sufficiency-v3'
            catalog = {e['evidence_id']: e for e in assessment['evidence_catalog']}
            for requirement in assessment['requirements']:
                for ref in requirement['references']:
                    entry = catalog[ref['evidence_id']]
                    assert ref['quote'] == entry['text'] == texts[ref['file_id']][ref['start_offset']:ref['end_offset']]
                    assert ref['page_indices'] == entry['page_indices']
review = json.loads((ROOT / 'reviewed-cases.json').read_text())
assert len(review['rows']) == 6
assert sum(len(r['points']) for r in review['rows']) == 16
claims = [c for r in review['rows'] for c in r['factual_claim_groups']]
assert len(claims) == 14 and sum(c['citation_coverage'] for c in claims) == 13
audit = json.loads((ROOT / 'assessment-reference-review.json').read_text())
assert audit['source_artifact_sha256'] == sha256((ROOT / audit['source_artifact']).read_bytes()).hexdigest()
assert audit['final_answer_review_sha256'] == sha256((ROOT / audit['final_answer_review_artifact']).read_bytes()).hexdigest()
metrics = json.loads((ROOT / 'measurement.json').read_text())
assert metrics['frozen_sha256'] == sha256((ROOT / 'frozen-cases.json').read_bytes()).hexdigest()
for group in [*metrics['groups'].values(), metrics['shared_preparation']]:
    assert set(group) == set(METRICS)
    for metric in group.values():
        assert metric['status'] in {'measured', 'not_applicable', 'unavailable'}
        if metric['status'] == 'measured':
            assert metric['value'] is not None and metric['unit'] is not None
        else:
            assert metric['value'] is None and metric['reason']
current = metrics['groups']['current-all']
assert current['Reliability']['value']['completed'] == 6
assert current['Citation coverage']['value'] == 13 / 14
assert all(current[k]['value'] == 1 for k in ['Answer correctness', 'Answer completeness', 'Final evidence coverage', 'Faithfulness', 'Citation support'])
for record in ['prepare-1', 'answers-1', 'retrieval-analysis-1', 'measurement-1']:
    assert json.loads((ROOT / f'{record}.json').read_text())['exit_code'] == 0
for path in ROOT.glob('*.py'):
    py_compile.compile(str(path), doraise=True)
secret = os.environ.get('OPENAI_API_KEY') or dotenv_values('.env').get('OPENAI_API_KEY')
for path in ROOT.rglob('*'):
    if path.is_file() and path.suffix in {'.json', '.jsonl', '.log', '.md', '.py'}:
        data = path.read_text()
        assert not secret or secret not in data, 'Credential leakage in retained artifact.'
documents = [Path('README.md'), Path('docs/evidence-sufficiency.md'), Path('docs/pdf-integration.md'),
             Path('docs/v2/README.md'), ROOT / 'README.md', ROOT / 'protocol.md']
links = 0
for path in documents:
    content = path.read_text()
    assert not any(line.rstrip() != line for line in content.splitlines()), path
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', content):
        if target.startswith(('http:', 'https:', '#')):
            continue
        target = target.split('#')[0]
        assert (path.parent / unquote(target)).exists(), (path, target)
        links += 1
subprocess.run(['git', 'diff', '--check'], check=True)
process = subprocess.run(['ps', '-p', '98234', '-o', 'command='], capture_output=True, text=True)
assert '20260927-financial-acceptance/server.py' not in process.stdout
print(f'Verified six streamed/saved answers, 16 reviewed points, 14 claim groups, exact source references, seven complete 20-metric inventories, frozen hashes, {links} local links, credential redaction and stopped evaluation server.')
