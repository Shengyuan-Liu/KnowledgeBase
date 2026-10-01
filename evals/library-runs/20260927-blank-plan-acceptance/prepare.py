"""Freeze clean product code and the reused-index six-request acceptance runtime."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import socket
import subprocess

from knowledgebase.config import Settings
from clone_index import DATA, SOURCE, manifest

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT.parent / '20260927-table-cell-context-acceptance'
PDF = Path('evals/materials/pdf-v2/background-checks.pdf')
assert not (ROOT / 'preparation.json').exists(), 'Preserve prior attempts.'
assert subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip() == 'v2'
assert not subprocess.check_output(['git', 'diff', 'HEAD', '--', 'knowledgebase', 'pyproject.toml', 'uv.lock'], text=True), 'Commit product implementation first.'
with socket.socket() as connection:
    assert connection.connect_ex(('127.0.0.1', 8786)) != 0
reuse = json.loads((ROOT / 'index-reuse.json').read_text())
assert manifest(DATA) == reuse['source_file_hashes'] == manifest(SOURCE)
settings = Settings(openai_timeout_seconds=180, openai_max_retries=0)
assert settings.openai_api_key.strip()
cases = json.loads((ROOT / 'frozen-cases.json').read_text())
assert len(cases['cases']) == 3
assert all(case['files'] == ['background-checks.pdf'] and case['followup_of'] is None for case in cases['cases'])
assert (ROOT / 'frozen-cases.json').read_bytes() == (BASELINE / 'frozen-cases.json').read_bytes()
assert (ROOT / 'frozen-original-protocol.md').read_bytes() == (BASELINE / 'frozen-original-protocol.md').read_bytes()
assert (ROOT / 'frozen-fact-labels.json').read_bytes() == (BASELINE / 'frozen-fact-labels.json').read_bytes()
assert sha256(PDF.read_bytes()).hexdigest() == '4f0ae6e017b0e97de211da8fd97316e55bd927af5740d6ce95e1b7b1539f9407'
baseline_settings = json.loads((BASELINE / 'resolved-runtime.json').read_text())['settings']
safe = settings.model_dump(mode='json', exclude={'openai_api_key', 'openai_base_url'})
safe['data_dir'] = str(DATA)
assert {k: v for k, v in safe.items() if k != 'data_dir'} == {k: v for k, v in baseline_settings.items() if k != 'data_dir'}, 'Disclose runtime drift before launching.'
record = {
    'at': datetime.now(timezone.utc).isoformat(), 'code_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'device': platform.platform(), 'data_directory': str(DATA), 'fresh_index_required': False,
    'index_reused': True, 'index_reuse_record': 'index-reuse.json', 'existing_library_modified': False,
    'source_file': str(PDF), 'source_sha256': sha256(PDF.read_bytes()).hexdigest(),
    'frozen_inputs': {str(p): sha256(p.read_bytes()).hexdigest() for p in [ROOT / 'protocol.md', ROOT / 'frozen-original-protocol.md', ROOT / 'frozen-cases.json', ROOT / 'frozen-fact-labels.json', ROOT / 'frozen-gold.json', ROOT / 'baseline-index-snapshot.json', PDF]},
    'harness_hashes': {p.name: sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.py')},
    'production_hashes': {str(p): sha256(p.read_bytes()).hexdigest() for p in Path('knowledgebase').rglob('*.py')},
    'env_file_sha256': sha256(Path('.env').read_bytes()).hexdigest(), 'settings': safe,
    'credential_authorization': 'User previously explicitly authorized use of the existing key; no credentials changed.',
    'request_count': 6, 'concurrency': 1, 'provider_retries': 0, 'provider_timeout_seconds': 180, 'client_timeout_seconds': 240,
    'provider_calls_during_preparation': 0,
    'comparison_limit': 'Same frozen six question/mode pairs, PDF bytes, indexed extraction and embeddings, fact annotations and runtime. Empty-cell wording and decomposed planner coverage completion changed; parser, scope and index unchanged; generated plans and rankings may differ. This is a development regression subset, not held-out generalization.',
    'ingestion': {'status': 'not_applicable', 'reason': 'Copied baseline index; no upload, parse or embedding request.'},
}
(ROOT / 'preparation.json').write_text(json.dumps(record, indent=2) + '\n')
print('Frozen exact baseline questions, rubric, labels, reused index, committed product code and safe runtime settings. Existing credential retained without disclosure.')
