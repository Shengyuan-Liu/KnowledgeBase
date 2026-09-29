"""Freeze the source-grounded workload and current runtime before provider calls."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import subprocess

from knowledgebase.config import Settings
from clone_index import DATA, SOURCE, manifest

ROOT = Path(__file__).resolve().parent

if __name__ == '__main__':
    assert not (ROOT / 'preparation.json').exists()
    assert subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip() == 'v2'
    assert not subprocess.check_output(['git', 'diff', 'HEAD', '--', 'knowledgebase', 'pyproject.toml', 'uv.lock'], text=True)
    reuse = json.loads((ROOT / 'index-reuse.json').read_text())
    assert manifest(SOURCE) == reuse['source_file_hashes']
    assert manifest(DATA) == json.loads((ROOT/'parent-rebuild.json').read_text())['after_file_hashes']
    cases = json.loads((ROOT / 'frozen-cases.json').read_text())
    settings = Settings(openai_timeout_seconds=180, openai_max_retries=0)
    assert settings.openai_api_key.strip()
    safe = settings.model_dump(mode='json', exclude={'openai_api_key', 'openai_base_url'})
    safe['data_dir'] = str(DATA)
    inputs = [ROOT / 'protocol.md', ROOT / 'frozen-cases.json', ROOT / 'baseline-index-snapshot.json', ROOT / 'rebuilt-index-snapshot.json', ROOT / 'frozen-labels.json']
    for document in cases['corpus']:
        path = Path('evals/materials/pdf-v2') / document['file']
        assert sha256(path.read_bytes()).hexdigest() == document['sha256']
        inputs.append(path)
    inputs.extend((ROOT.parent / '20260929-new-pdf-chain' / 'source-review').glob('*.png'))
    record = dict(
        at=datetime.now(timezone.utc).isoformat(),
        code_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        device=platform.platform(), settings=safe,
        frozen_inputs={str(p): sha256(p.read_bytes()).hexdigest() for p in inputs},
        production_hashes={str(p): sha256(p.read_bytes()).hexdigest() for p in Path('knowledgebase').rglob('*.py')},
        harness_hashes={p.name: sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.py')},
        env_file_sha256=sha256(Path('.env').read_bytes()).hexdigest(),
        credential_authorization='Existing credential explicitly authorized by the user; no credentials changed or disclosed.',
        request_count=6, concurrency=1, provider_retries=0,
        provider_timeout_seconds=180, client_timeout_seconds=240,
        provider_calls_during_preparation=0,
        source_review=dict(reviewer='Codex (model)', rendered_pages=7, method='Reuse frozen prior original-page reference review; compare every new answer to retained source pages and exact supplied context.',
                           absence_limit='Not an exhaustive visual search of embedded lecture images.',
                           render_command='pdftoppm -f PAGE -l PAGE -singlefile -scale-to 1500 -png SOURCE OUTPUT'),
        scope='Matched six-question parent-context acceptance against 20260929-new-pdf-chain. Rebuild parents in an isolated five-PDF copy; preserve extraction, children, embeddings, facts and questions. No upload or parsing.',
    )
    (ROOT / 'preparation.json').write_text(json.dumps(record, indent=2) + '\n')
    print('Frozen six questions, original-page references, committed product code and credential-free settings.')
