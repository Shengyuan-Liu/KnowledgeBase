"""Compare canonical outputs; report local timings separately from equivalence."""

from copy import deepcopy
import json
from pathlib import Path
import platform
from statistics import mean

DIRECTORY = Path(__file__).parent
before = json.loads((DIRECTORY / 'before-2.json').read_text())
after = json.loads((DIRECTORY / 'after-1.json').read_text())
comparisons = []
for group, timing in [('documents', 'local_adapter_and_chunk_seconds'), ('queries', 'local_search_and_pack_seconds')]:
    for old, new in zip(before[group], after[group], strict=True):
        old, new = deepcopy(old), deepcopy(new)
        old.pop(timing)
        new.pop(timing)
        if group == 'queries':
            for row in (old, new):
                row['supplied']['diagnostics'].pop('packing_seconds')
                for hit in row['supplied']['chunks']:
                    # Old RetrievedChunk serialized only the six base Chunk fields.
                    # These structural values are compared on canonical chunks above.
                    for key in ['heading_path', 'source_block_indices', 'token_count', 'tokenizer', 'max_tokens']:
                        hit['chunk'].pop(key, None)
        comparisons.append({'group': group, 'case': old.get('name', old.get('question')),
                            'identical': old == new})
assert before['inputs'] == after['inputs']
(DIRECTORY / 'comparison-2.json').write_text(json.dumps(comparisons, indent=2) + '\n')
assert all(row['identical'] for row in comparisons), comparisons
inventory = json.loads((DIRECTORY / 'replay-after-1.json').read_text())['metric_inventory']

def stats(values):
    values = sorted(values)
    def percentile(q):
        index = (len(values) - 1) * q
        lower = int(index)
        return values[lower] + (values[min(lower + 1, len(values) - 1)] - values[lower]) * (index - lower)
    return {'samples': len(values), 'mean_seconds': mean(values), 'p50_seconds': percentile(.5),
            'p95_seconds': percentile(.95), 'percentile_method': 'linear interpolation'}

stages = {name: {label: stats([row[key] for row in arm[group]]) for label, arm in [('before', before), ('after', after)]}
          for name, group, key in [('frozen_adapter_and_chunk', 'documents', 'local_adapter_and_chunk_seconds'),
                                    ('lexical_search_and_pack', 'queries', 'local_search_and_pack_seconds')]}
inventory['Stage latency'] = {
    'status': 'measured', 'value': stages, 'unit': 'seconds',
    'reason': 'Offline local stages only. Frozen Docling JSON validation, adaptation and chunking; then BM25 top-20 search and top-5 evidence packing. No model conversion, embeddings, reranking or generation.',
    'sample_count': {'documents_per_arm': 5, 'questions_per_arm': 16},
    'population': 'Matched frozen PDF workload; one sequential pass per arm.',
    'method': 'perf_counter; imports excluded; first tokenizer cache initialization included; no queue or warmup. Concurrency 1.',
    'aggregation': 'mean, P50 and P95 with linear interpolation',
    'artifact': 'before-2.json; after-1.json',
}
report = {
    'baseline_commit': 'dea314a', 'after_identity': 'replay-after-1.json changed_and_tracked_file_hashes',
    'reviewer': 'Codex', 'method': 'Exact equality of normalized source payload, chunk spans/metadata, rankings/scores, packed evidence and rendered context. Not human answer grading.',
    'normalization': 'Exclude separately measured packing time and added serialized structural Chunk fields; compare those fields on the complete canonical chunk sets instead. Map old parent.parent_id to chunk_id; remove new Chunk.type and the parent_id field on expanded context spans. Preserve all canonical text, IDs, offsets, page regions, table metadata, parser identity and revision hashes.',
    'device': platform.platform(), 'provider_calls': 0,
    'results': {'pdf_payloads_and_chunk_sets_identical': [5, 5], 'rankings_and_supplied_evidence_identical': [16, 16],
                'changed_contexts': 0},
    'limits': 'No relevance annotations are newly scored. This comparison establishes fixture equivalence, not retrieval quality, live answer quality or production performance. Timing diagnostics are a single local pass and support no speed claim.',
    'metric_inventory': inventory,
}
(DIRECTORY / 'measurement.json').write_text(json.dumps(report, indent=2) + '\n')
print('Identical: 5/5 PDF payloads and chunk sets; 16/16 rankings, supplied evidence and contexts.')
