"""Audit canonical slices, context budgets, metadata and citation syntax offline."""

import importlib.util
import json
from pathlib import Path
import re
import sys

import tiktoken

from evals.evaluate import retrieval_metrics
from knowledgebase.rag.context import build_context
from knowledgebase.schemas import StructuredChunk, RetrievedChunk


def run(root):
    files = json.loads((root / 'chunks.json').read_text())
    canonical = {c.get('chunk_id', c.get('parent_id')): c for f in files for c in [*f['chunks'], *f['parents']]}
    spec = importlib.util.spec_from_file_location('baseline', root / 'baseline_context.py')
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    encoding = tiktoken.get_encoding('cl100k_base')
    records = []
    for row in map(json.loads, (root / 'answers.jsonl').read_text().splitlines()):
        chunks = []
        for source in row['sources']:
            original = canonical[source['chunk_id']]
            for key in ['text', 'file_id', 'heading_path', 'start_offset', 'end_offset']:
                assert source[key] == original[key]
            chunks.append(RetrievedChunk(chunk=StructuredChunk.model_validate(source),
                                         file_name=source['file_name'], distance=source['distance']))
        formatter = baseline.build_context if row['strategy'] == 'baseline' else build_context
        context = formatter(chunks)
        assert row['messages'][1]['content'].split('\n\nSources:\n', 1)[1] == context
        assert len(encoding.encode_ordinary(context)) == row['retrieval']['evidence_tokens'] <= 4096
        cited = list(dict.fromkeys(int(n) for n in re.findall(r'\[([0-9]+)\]', row['answer'])))
        invalid = [n for n in cited if n not in {s['source_id'] for s in row['sources']}]
        malformed = re.findall(r'\[(?:cite|source)\s*:?\s*\d+[^\]]*\]', row['answer'], re.I)
        records.append({'case_id': row['case_id'], 'strategy': row['strategy'],
                        'canonical_slices_and_metadata_match': True, 'budget_matches_actual_model_context': True,
                        'context_format': row['retrieval']['context_format'],
                        'identity_overhead_tokens_for_same_sources': len(encoding.encode_ordinary(build_context(chunks)))
                            - len(encoding.encode_ordinary(baseline.build_context(chunks))),
                        'valid_citation_ids': [n for n in cited if n not in invalid],
                        'invalid_citation_ids': invalid, 'nonstandard_citation_forms': malformed,
                        'raw_metadata_in_answer': '"file_name"' in row['answer'] or '"heading_path"' in row['answer'],
                        'citation_check_scope': 'Syntax only, not semantic support or claim coverage.'})
    with (root / 'source-audit.json').open('x') as out:
        json.dump(records, out, indent=2)
    if (root / 'app-smoke.json').exists():
        smoke = json.loads((root / 'app-smoke.json').read_text())
        answer = smoke['events'][-1]['data']
        case = next(c for c in json.loads((root / 'cases.json').read_text()) if c['id'] == 'msds-cpt-source-context')
        case = {**case, 'evidence': [{**e, 'file': Path(e['file']).name} for e in case['evidence']]}
        names = json.loads((root / 'metrics.json').read_text())['candidate']
        metrics = {name: {'status': 'unavailable', 'value': None,
                         'reason': 'Single route smoke; full measurement or semantic adjudication not performed.'} for name in names}
        def measured(value, method):
            return {'status': 'measured', 'value': value, 'n': 1, 'method': method, 'artifact': 'app-smoke.json'}
        for metric, field in [('first_answer_delta_latency', 'first_delta_seconds'), ('complete_response_latency', 'total_seconds')]:
            metrics[metric] = measured({k: smoke[field] for k in ['mean', 'p50', 'p95']},
                                      'Actual app HTTP seconds; n=1, no population percentile claim.')
        metrics['final_evidence_coverage'] = measured(retrieval_metrics(case, answer['sources']), 'Exact annotated CPT spans.')
        metrics['stage_latency'] = measured({k: answer['retrieval'][k] for k in ['rerank_seconds', 'packing_seconds']},
                                           'Seconds; other stage timers unavailable.')
        metrics['reliability'] = measured({'success': 1, 'errors': 0, 'requests': 1}, 'Actual HTTP request completion.')
        metrics['concurrency_and_throughput'] = measured({'concurrency': 1, 'requests_per_active_second': 1 / smoke['total_seconds']},
                                                        'One request, not a load capacity measurement.')
        metrics['ingestion_and_index'] = {'status': 'not_applicable', 'value': None,
                                         'reason': 'No index mutation; files and old history checked unchanged.'}
        with (root / 'app-smoke-metrics.json').open('x') as out:
            json.dump(metrics, out, indent=2)
    print(root.name, 'audited', len(records), 'contexts;',
          sum(bool(r['nonstandard_citation_forms']) for r in records), 'nonstandard citation outputs')


if __name__ == '__main__':
    run(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent)
