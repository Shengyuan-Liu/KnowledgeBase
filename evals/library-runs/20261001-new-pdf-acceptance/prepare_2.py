"""Verify sealed inputs and record credential-free execution settings."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import subprocess
from knowledgebase.config import Settings
ROOT=Path(__file__).resolve().parent
MATERIAL=Path('evals/materials/pdf-v2-candidate-20261001')
DATA=Path('data/evals/20261001-new-pdf-acceptance-2').resolve()
def write(name,value):
    with (ROOT/name).open('x') as f: f.write(json.dumps(value,indent=2)+'\n')
if __name__=='__main__':
    freeze=json.loads((MATERIAL/'freeze.json').read_text())
    for kind in ['input_hashes','product_hashes']:
        assert all(sha256(Path(p).read_bytes()).hexdigest()==v for p,v in freeze[kind].items()),kind
    assert not DATA.exists()
    assert subprocess.check_output(['git','branch','--show-current'],text=True).strip()=='v2'
    settings=Settings(openai_timeout_seconds=180,openai_max_retries=0)
    assert settings.openai_api_key.strip()
    safe=settings.model_dump(mode='json',exclude={'openai_api_key','openai_base_url'});safe['data_dir']=str(DATA)
    write('preparation-2.json',dict(at=datetime.now(timezone.utc).isoformat(),code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),device=platform.platform(),settings=safe,frozen_inputs=freeze['input_hashes'],production_hashes=freeze['product_hashes'],harness_hashes={p.name:sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.py')},env_file_sha256=sha256(Path('.env').read_bytes()).hexdigest(),credential_authorization='Existing key explicitly authorized by user; no credential changes.',request_count=6,concurrency=1,provider_retries=0,provider_timeout_seconds=180,client_timeout_seconds=240,provider_calls_during_preparation=0,scope='Fresh four-PDF 90-page library; one pass through six frozen questions and browser acceptance. No comparison to different-corpus prior scores.'))
    print('1 passed: sealed inputs and product hashes match; empty isolated data path; credential present.')
