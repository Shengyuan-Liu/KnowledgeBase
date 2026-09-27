"""Verify the completed live record and documentation without further model calls."""
from hashlib import sha256
import json
import os
from pathlib import Path
import py_compile
import re
import socket
import subprocess
from urllib.parse import unquote

from dotenv import dotenv_values
from record_check import METRICS

ROOT = Path(__file__).parent
PRIOR = ROOT.parent / '20260927-financial-acceptance'
ORIGINAL = ROOT.parent / '20260927-v2-pdf-live'
frozen = json.loads((ROOT / 'frozen-cases.json').read_text())
assert (ROOT / 'frozen-cases.json').read_bytes() == (PRIOR / 'frozen-cases.json').read_bytes()
snapshot = json.loads((ORIGINAL / 'index-snapshot.json').read_text())
texts = {d['file']['file_id']: d['extraction']['text'] for d in snapshot['files']}
runtime = json.loads((ROOT / 'resolved-runtime.json').read_text())
prior_runtime = json.loads((PRIOR / 'resolved-runtime.json').read_text())
assert {k: v for k, v in runtime['settings'].items() if k != 'data_dir'} == {
    k: v for k, v in prior_runtime['settings'].items() if k != 'data_dir'}
assert runtime['reranker'] == prior_runtime['reranker']
for path, digest in runtime['source_hashes'].items():
    assert sha256(Path(path).read_bytes()).hexdigest() == digest, path
for name in ['server.py', 'run.py', 'observability.py', 'prepare.py', 'record_check.py']:
    assert sha256((ROOT / name).read_bytes()).hexdigest() == runtime['harness_hashes'][name], name
preparation = json.loads((ROOT / 'preparation.json').read_text())
assert preparation['protocol_sha256'] == sha256((ROOT / 'protocol.md').read_bytes()).hexdigest()
assert preparation['copy_byte_identical'] and preparation['provider_calls'] == preparation['regenerated_vectors'] == 0
assert preparation['source_file_hashes'] == preparation['cloned_file_hashes_before_open']
for name, digest in preparation['source_file_hashes'].items():
    assert sha256((Path(preparation['source_directory']) / name).read_bytes()).hexdigest() == digest
for case in frozen['cases']:
    for arm in ['single', 'planned']:
        row = json.loads((ROOT / f"{case['id']}-{arm}.json").read_text())
        assert row['status'] == 'completed' and row['request']['question'] == case['question']
        assert row['history_matches'] and row['history_retrieval_matches']
        assert row['first_answer_delta_seconds'] <= row['complete_response_seconds']
        answer = row['answer']
        assert ''.join(e['data']['delta'] for e in row['events'] if e['data']['event'] == 'answer_delta') == answer['answer']
        assert answer['sources'] == [{k: v for k, v in source.items() if k != 'file_deleted'}
                                     for source in row['saved_message']['sources']]
        for source in answer['sources']:
            assert source['text'] == texts[source['file_id']][source['start_offset']:source['end_offset']]
            for supplement in source['pdf']['supplements']:
                assert supplement['text'] == texts[source['file_id']][supplement['start_offset']:supplement['end_offset']]
        if arm == 'planned':
            assessment = answer['retrieval']['planning']['assessment']
            catalog = {e['evidence_id']: e for e in assessment['evidence_catalog']}
            for requirement in assessment['requirements']:
                selected = {r['evidence_id'] for r in requirement['references']}
                for ref in [*requirement['references'], *requirement['table_context']]:
                    entry = catalog[ref['evidence_id']]
                    assert ref['quote'] == entry['text'] == texts[ref['file_id']][ref['start_offset']:ref['end_offset']]
                    assert ref['page_indices'] == entry['page_indices']
                for ref in requirement['table_context']:
                    assert ref['evidence_id'] not in selected and set(ref['for_evidence_ids']) <= selected
review = json.loads((ROOT / 'reviewed-cases.json').read_text())
assert len(review['rows']) == 6 and sum(len(r['points']) for r in review['rows']) == 16
claims = [c for r in review['rows'] for c in r['factual_claim_groups']]
assert len(claims) == 16 and sum(c['citation_coverage'] for c in claims) == 16
for row in review['rows']:
    answer = json.loads((ROOT / f"{row['case_id']}-{row['arm']}.json").read_text())['answer']['answer']
    assert all(claim['text'] in answer for claim in row['factual_claim_groups'])
assert 'inference allowance' in review['review_scope']
for name in ['assessment-reference-review.json', 'citation-qualifier-audit.json']:
    audit = json.loads((ROOT / name).read_text())
    assert audit['final_answer_review_sha256'] == sha256((ROOT / audit['final_answer_review_artifact']).read_bytes()).hexdigest()
metrics = json.loads((ROOT / 'measurement.json').read_text())
for group in [*metrics['groups'].values(), metrics['shared_preparation']]:
    assert set(group) == set(METRICS)
    for metric in group.values():
        assert metric['status'] in {'measured', 'not_applicable', 'unavailable'}
        assert (metric['value'] is not None) == (metric['status'] == 'measured')
        if metric['status'] != 'measured':
            assert metric['reason']
assert all(gate['passed'] for gate in metrics['scoped_gates']['current'].values())
for name in ['prepare-2', 'answers-1', 'retrieval-analysis-1', 'measurement-1']:
    assert json.loads((ROOT / f'{name}.json').read_text())['exit_code'] == 0
assert json.loads((ROOT / 'prepare-1.json').read_text())['exit_code'] != 0
for path in ROOT.glob('*.py'):
    py_compile.compile(str(path), doraise=True)
secret = os.environ.get('OPENAI_API_KEY') or dotenv_values('.env').get('OPENAI_API_KEY')
for path in ROOT.rglob('*'):
    if path.is_file() and path.suffix in {'.json', '.jsonl', '.log', '.md', '.py'}:
        assert not secret or secret not in path.read_text(), 'Credential leakage in retained artifact.'
documents = [Path('README.md'), Path('docs/answer-grounding.md'), Path('docs/evidence-sufficiency.md'),
    Path('docs/pdf-integration.md'), Path('docs/v2/README.md'), ROOT / 'README.md', ROOT / 'protocol.md']
links = 0
for path in documents:
    content = path.read_text()
    assert not any(line.rstrip() != line for line in content.splitlines()), path
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', content):
        if target.startswith(('http:', 'https:', '#')):
            continue
        assert (path.parent / unquote(target.split('#')[0])).exists(), (path, target)
        links += 1
subprocess.run(['git', 'diff', '--check'], check=True)
with socket.socket() as connection:
    connection.settimeout(1)
    assert connection.connect_ex(('127.0.0.1', 8785)) != 0
print(f'Verified six streamed/saved answers, 16 requested points and 16 reviewed claim groups under the frozen rubric, exact selected/attached source spans, complete metric inventories, preserved source index, frozen runtime, {links} documentation links and stopped server. No additional provider calls.')
