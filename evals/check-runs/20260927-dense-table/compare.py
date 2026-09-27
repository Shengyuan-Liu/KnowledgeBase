"""Compare immutable parser revisions and real local parsing on frozen PDF bytes."""
from hashlib import sha256
import json
from pathlib import Path
import platform
import runpy
import subprocess
import sys
import time
import traceback

from docling_core.types.doc import DoclingDocument
from knowledgebase.rag.pdf import PdfParser, adapt_pdf_document
from knowledgebase.rag.pdf_tables import recover_collapsed_tables
from record_check import METRICS

DIRECTORY = Path(__file__).resolve().parent
ROOT = DIRECTORY.parents[2]
OUT = DIRECTORY / sys.argv[1]
OUT.mkdir()
GOLD = json.loads((DIRECTORY / 'gold.json').read_text())
CORPUS = ROOT / 'evals/materials/pdf-v2'
FROZEN = ROOT / 'evals/check-runs/20260926-pdf-parser-selection'


def save(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def normalize(text):
    return ' '.join((text or '').split())


def review(extraction):
    table = next(b.table for b in extraction.blocks if b.table)
    paths = [[normalize(c.text) for c in table.cells if c.column_header and c.text.strip()
              and c.column_start <= col < c.column_end and c.column_end - c.column_start < table.columns]
             for col in range(table.columns)]
    path_matches = [col < len(paths) and paths[col] == path for col, path in enumerate(GOLD['table']['header_paths'])]
    rows = []
    for expected in GOLD['table']['rows']:
        labels = [c for c in table.cells if normalize(c.text) == expected['label'] and c.column_start == 0]
        row = labels[0].row_start if len(labels) == 1 else None
        cells = []
        for col, value in enumerate(expected['values']):
            found = [c for c in table.cells if c.row_start == row and c.column_start == col and c.column_end == col + 1]
            cell = found[0] if len(found) == 1 else None
            cells.append({'column': col, 'expected': value, 'observed': cell.text if cell else None,
                          'cell': cell.model_dump(mode='json') if cell else None,
                          'match': bool(cell is not None and normalize(cell.text) == normalize(value) and path_matches[col])})
        rows.append({'label': expected['label'], 'row': row, 'cells': cells, 'exact': all(c['match'] for c in cells)})
    cells = [c for row in rows for c in row['cells']]
    groups = [{'label': normalize(c.text), 'column_start': c.column_start, 'column_end': c.column_end}
              for c in table.cells if c.column_header and c.text.strip() and 1 < c.column_end - c.column_start < table.columns]
    counts = {
        'numeric_cells': [sum(c['match'] for c in cells if c['column'] and c['expected'] is not None), 66],
        'explicit_blanks': [sum(c['match'] for c in cells if c['expected'] is None), 6],
        'row_labels': [sum(c['match'] for c in cells if c['column'] == 0), 3],
        'header_paths': [sum(path_matches), 25],
        'merged_groups': [sum(g in groups for g in GOLD['table']['merged_header_groups']), 6],
        'exact_rows': [sum(r['exact'] for r in rows), 3],
        'original_four_facts': [sum(rows[0]['cells'][c]['match'] for c in [1, 2, 3, 24]), 4],
    }
    controls = [{'id': c['id'], 'match': all(normalize(p) in normalize(extraction.text)
                for p in c.get('required_phrases', [c.get('expected_text')]))} for c in GOLD['document_controls']]
    return {'counts': counts, 'rows': rows, 'header_paths': paths, 'merged_groups': groups, 'document_controls': controls}


def timing(value):
    return {'n': 1, 'mean_seconds': value, 'p50_seconds': value, 'p95_seconds': value,
            'percentile_method': 'One observation; all percentiles equal the observed value.'}


started = time.perf_counter()
state = {'command': sys.argv, 'baseline_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
         'device': platform.platform(), 'concurrency': 1, 'threads': 4, 'retries': 0, 'timeout': None,
         'cache': 'Local model files already present; OS cache uncontrolled. Sequential parser instances; first parse of each includes model loading; no queue.',
         'reviewer': 'Codex model reviewer; deterministic comparison to independent visual transcription in gold.json.',
         'inputs': {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in [DIRECTORY / 'gold.json', DIRECTORY / 'baseline-pdf.py', *CORPUS.glob('*.pdf')]},
         'implementation': {str(p): sha256(p.read_bytes()).hexdigest() for p in [Path('knowledgebase/rag/pdf.py'), Path('knowledgebase/rag/pdf_tables.py'), Path('pyproject.toml'), Path('uv.lock')]},
         'cases': [], 'original_parses': [], 'metric_inventory': {m: {'status': 'not_applicable', 'value': None,
             'unit': None, 'reason': 'Offline parser comparison; no queries, model answers, provider calls, upload/index lifecycle, or production load.',
             'sample_count': 0, 'population': 'local parser comparison', 'method': 'not exercised', 'aggregation': 'none', 'artifact': 'run.json'} for m in METRICS}}
save('run.json', state)
try:
    before_parser = runpy.run_path(str(DIRECTORY / 'baseline-pdf.py'))['PdfParser'](ROOT / 'data/pdf-models')
    after_parser = PdfParser(ROOT / 'data/pdf-models')
    save('before-identity.json', before_parser.identity.model_dump(mode='json'))
    save('after-identity.json', after_parser.identity.model_dump(mode='json'))
    for name in ['background-checks', 'apple-fy24', 'doclaynet', 'ml-lecture', 'docling-report']:
        path = FROZEN / ('apple-1' if name == 'apple-fy24' else 'attempt-1') / f'{name}-docling.json'
        source = (CORPUS / f'{name}.pdf').read_bytes()
        doc = DoclingDocument.model_validate_json(path.read_text())
        before = adapt_pdf_document(doc, source, before_parser.identity)
        start = time.perf_counter()
        recovered = recover_collapsed_tables(doc, source)
        recovery_seconds = time.perf_counter() - start
        after = adapt_pdf_document(doc, source, after_parser.identity, recovered_tables=recovered)
        save(f'{name}-before.json', before.model_dump(mode='json'))
        save(f'{name}-after.json', after.model_dump(mode='json'))
        case = {'case': name, 'frozen_docling': str(path.relative_to(ROOT)), 'frozen_docling_sha256': sha256(path.read_bytes()).hexdigest(),
                'recovered_tables': recovered, 'recovery_stage': timing(recovery_seconds), 'canonical_text_unchanged': before.text == after.text,
                'blocks_unchanged': before.blocks == after.blocks, 'source_hash_unchanged': before.source_hash == after.source_hash}
        if name == 'background-checks':
            for label, result in [('before', before), ('after', after)]:
                save(f'review-{label}.json', review(result))
            case['before_scores'] = review(before)['counts']
            case['after_scores'] = review(after)['counts']
            assert all(n == d for n, d in case['after_scores'].values())
            assert all(c['match'] for c in review(after)['document_controls'])
        else:
            assert not recovered and case['canonical_text_unchanged'] and case['blocks_unchanged']
        state['cases'].append(case)
        save('run.json', state)
    for label, parser in [('before', before_parser), ('after', after_parser)]:
        start = time.perf_counter()
        result = parser.parse((CORPUS / 'background-checks.pdf').read_bytes())
        elapsed = time.perf_counter() - start
        save(f'original-{label}.json', result.model_dump(mode='json'))
        score = review(result)
        save(f'original-{label}-review.json', score)
        state['original_parses'].append({'variant': label, 'parse_stage': timing(elapsed), 'status': 'success', 'scores': score['counts']})
        save('run.json', state)
        if label == 'after':
            assert all(n == d for n, d in score['counts'].values())
            assert all(c['match'] for c in score['document_controls'])
            assert any(w.code == 'native_table_recovery' for w in result.warnings)
    state['status'] = 'success'
except Exception:
    state['status'] = 'error'
    state['error'] = traceback.format_exc()
    raise
finally:
    state['duration_seconds'] = time.perf_counter() - started
    for metric, value, reason, samples in [
        ('Stage latency', {'native_recovery': [c['recovery_stage'] for c in state['cases']], 'original_parser': state['original_parses']}, 'Only parser stages; first parse includes local model loading, no queue or provider.', len(state['cases']) + len(state['original_parses'])),
        ('Reliability', {'completed_replays': len(state['cases']), 'completed_original_parses': len(state['original_parses']), 'errors': int(state.get('status') == 'error'), 'timeouts': 0, 'retries': 0}, 'Offline command and parse completion; fidelity scored separately.', len(state['cases']) + len(state['original_parses'])),
        ('Concurrency and throughput', {'concurrency': 1, 'completed_cases_per_second': (len(state['cases']) + len(state['original_parses'])) / state['duration_seconds']}, 'Whole comparison command including identity hashing, JSON recording and review; not production load capacity.', len(state['cases']) + len(state['original_parses'])),
    ]:
        state['metric_inventory'][metric].update(status='measured', value=value, unit='structured observations', reason=reason,
            sample_count=samples, method='perf_counter and retained result counts', aggregation='per case')
    save('run.json', state)
    print(json.dumps({'status': state.get('status'), 'cases': state['cases'], 'original_parses': state['original_parses']}, indent=2))
