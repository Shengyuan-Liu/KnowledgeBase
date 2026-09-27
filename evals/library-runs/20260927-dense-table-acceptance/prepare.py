"""Freeze a six-request live protocol and isolate a fresh PDF index."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import socket
import subprocess

from knowledgebase.config import Settings

ROOT = Path(__file__).resolve().parent
DATA = Path('data/evals/20260927-dense-table-acceptance').resolve()
SOURCE = Path('evals/materials/pdf-v2/background-checks.pdf')
assert not DATA.exists(), 'A fresh index is required.'
assert not (ROOT / 'preparation.json').exists(), 'Preserve prior attempts.'
assert subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip() == 'v2'
assert not subprocess.check_output(['git', 'diff', 'HEAD', '--', 'knowledgebase', 'pyproject.toml', 'uv.lock'], text=True)
with socket.socket() as connection:
    assert connection.connect_ex(('127.0.0.1',8786)) != 0, 'Port is already occupied.'
settings = Settings(openai_timeout_seconds=180, openai_max_retries=0)
assert settings.openai_api_key.strip()
cases=json.loads((ROOT/'frozen-cases.json').read_text())
assert len(cases['cases']) == 3
assert all(case['files']==['background-checks.pdf'] and case['followup_of'] is None for case in cases['cases'])
assert sha256(SOURCE.read_bytes()).hexdigest() == '4f0ae6e017b0e97de211da8fd97316e55bd927af5740d6ce95e1b7b1539f9407'
record = {
    'at':datetime.now(timezone.utc).isoformat(), 'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
    'device':platform.platform(), 'data_directory':str(DATA), 'fresh_index_required':True,
    'existing_library_modified':False, 'source_file':str(SOURCE),'source_sha256':sha256(SOURCE.read_bytes()).hexdigest(),
    'frozen_inputs':{str(p):sha256(p.read_bytes()).hexdigest() for p in [ROOT/'protocol.md',ROOT/'frozen-cases.json',SOURCE]},
    'harness_hashes':{p.name:sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.py')},
    'production_hashes':{str(p):sha256(p.read_bytes()).hexdigest() for p in Path('knowledgebase').rglob('*.py')},
    'env_file_sha256':sha256(Path('.env').read_bytes()).hexdigest(),
    'settings':settings.model_dump(mode='json',exclude={'openai_api_key','openai_base_url'}),
    'credential_authorization':'User previously explicitly authorized use of the existing key; no credentials changed.',
    'request_count':6,'concurrency':1,'provider_retries':0,'provider_timeout_seconds':180,'client_timeout_seconds':240,
    'provider_calls_during_preparation':0,
    'comparison_limit':'Current single-PDF index and two new questions have no matching six-request live baseline. Historical original-question failure is contextual only; parser before/after is separately frozen.'
}
record['settings']['data_dir']=str(DATA)
(ROOT/'preparation.json').write_text(json.dumps(record,indent=2)+'\n')
print('Frozen three questions, source/protocol/code hashes and runtime settings; fresh isolated index reserved. Existing credential retained without disclosure.')
