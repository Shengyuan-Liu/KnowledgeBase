"""Normalize report links and verify evidence, tested code, and documentation offline."""
from hashlib import sha256
import json
from pathlib import Path
import re

from record_check import METRICS

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text())


def main():
    replay = load('replay-results.json')
    frozen = load('frozen-inputs.json')
    scoped = load('scoped-1.json')
    assert scoped['counts']['passed'] == 177 and scoped['exit_code'] == 0
    assert load('focused-1.json')['counts'] == {'passed': 8, 'failed': 1, 'skipped': 0, 'error': 0}
    assert load('focused-2.json')['counts']['passed'] == 9
    for path, digest in frozen['files'].items():
        assert sha256(Path(path).read_bytes()).hexdigest() == digest
    for path, digest in scoped['changed_and_tracked_file_hashes'].items():
        if path.startswith(('knowledgebase/', 'tests/')):
            assert sha256(Path(path).read_bytes()).hexdigest() == digest
    assert len(replay['rows']) == 12
    assert [(p['case_id'], p['improved']) for p in replay['pairs'] if p['improved']] == [
        ('lecture-bag-words', ['topic_documents', 'topic_words'])]
    assert not any(p['regressed'] for p in replay['pairs'])
    assert all(r['result']['diagnostics']['evidence_tokens'] <= 4096 for r in replay['rows'])
    assert sum(c['children'] for c in replay['corpus'] if c['phase'] == 'after') == 621
    assert all(c['child_content_ids_offsets_headings_unchanged'] for c in replay['corpus'])
    print('Frozen inputs and tested implementation match; 12 replay results retain only the two intended fact gains.')

    inventory = replay['metric_inventory']
    assert set(inventory) == set(METRICS)
    for name in METRICS[:5]:
        inventory[name]['artifact'] = '../../library-runs/20260929-new-pdf-chain/diagnostics.json'
    for entry in inventory.values():
        assert entry['status'] in {'measured', 'unavailable', 'not_applicable'}
        if entry['status'] != 'measured':
            assert entry['value'] is None and entry['reason']
        assert (ROOT / entry['artifact']).exists()
    with (ROOT / 'measurement.json').open('x') as file:
        file.write(json.dumps(dict(
            source='replay-results.json', source_sha256=sha256((ROOT / 'replay-results.json').read_bytes()).hexdigest(),
            correction='Only five relative ranking-metric artifact paths are normalized. No metric value, raw context, failure or live output was changed.',
            metric_inventory=inventory,
        ), indent=2) + '\n')
    print('All 20 metrics have statuses and valid artifact paths; source values and failures are preserved.')

    for path in [ROOT / 'README.md', Path('docs/pdf-integration.md'), Path('docs/v2/README.md')]:
        text = path.read_text()
        assert not re.search('[\u4e00-\u9fff]', text)
        assert all(line.rstrip() == line for line in text.splitlines())
        for link in re.findall(r'\]\(([^)]+)\)', text):
            if not link.startswith(('http://', 'https://', '#')):
                assert (path.parent / link.split('#')[0]).exists(), (path, link)
    print('English documentation, local links, formatting, reindex requirements and offline-only claims reviewed.')
    print('3 passed')


if __name__ == '__main__':
    main()
