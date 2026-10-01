"""Compare baseline runtime and freeze exact execution inputs before live answers."""
from hashlib import sha256
import json
from pathlib import Path
from labels import locations

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT.parent / '20260929-pdf-heading-acceptance'

if __name__ == '__main__':
    old = json.loads((BASELINE/'resolved-runtime.json').read_text())
    new = json.loads((ROOT/'resolved-runtime.json').read_text())
    differences = {key: {'before': old['settings'].get(key), 'after': value}
                   for key, value in new['settings'].items() if old['settings'].get(key) != value}
    assert set(differences) == {'data_dir'}, differences
    assert old['reranker'] == new['reranker'] and old['packages'] == new['packages']
    assert old['device'] == new['device'] and old['python'] == new['python']
    for name in ['frozen-cases.json','frozen-labels.json']:
        assert (ROOT/name).read_bytes() == (BASELINE/name).read_bytes()
    frozen = json.loads((ROOT/'frozen-cases.json').read_text())
    snapshot = json.loads((ROOT/'index-snapshot.json').read_text())
    assert locations(frozen['facts'], snapshot['files']) == json.loads((ROOT/'frozen-labels.json').read_text())
    record = dict(settings_differences=differences, reranker_packages_device_python_equal=True,
        source_questions_labels_equal=True, fact_locations_equal=True,
        baseline_commit=old['code_commit'], current_commit=new['code_commit'],
        source_hashes=new['source_hashes'], harness_hashes={p.name:sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.py')},
        request_count=6, retries=0, concurrency=1,
        baseline_input_hashes={name:sha256((BASELINE/name).read_bytes()).hexdigest() for name in
            ['frozen-cases.json','frozen-labels.json','resolved-runtime.json','index-snapshot.json','diagnostics.json','review.json','measurement.json']})
    with (ROOT/'answer-execution-manifest.json').open('x') as file:
        file.write(json.dumps(record,indent=2)+'\n')
    print('Runtime matches baseline except isolated data path; models, packages, reranker device, budgets, questions and source-span labels match. Ready for exactly six live requests.')
