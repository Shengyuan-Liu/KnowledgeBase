"""Append-only diagnostics and reviewed-score aggregation for this frozen workload."""
from collections import Counter, defaultdict
from datetime import datetime
from hashlib import sha256
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).parent
FROZEN = json.loads((ROOT / 'effective-cases.json').read_text())
INDEX = json.loads((ROOT / 'index-snapshot.json').read_text())
FILES = {d['file']['file_name']: d for d in INDEX['files']}
CHUNKS = {c['chunk_id']: c for d in INDEX['files'] for c in d['chunks']}


def write(name, value):
    path = ROOT / name
    assert not path.exists(), f'Append-only: {path}'
    path.write_text(json.dumps(value, indent=2) + '\n')


def locations():
    result = {}
    for identity, fact in FROZEN['facts'].items():
        document = FILES[fact['file']]
        # Anchor sets may span adjacent blocks, e.g. the two lecture-book bullets.
        # Map each anchor independently on an annotated physical page, then require
        # every anchor for fact recall. Candidate relevance only requires a touch.
        anchors = []
        for anchor in fact['anchors']:
            spans = []
            for block in document['extraction']['blocks']:
                if not {r['page_index'] + 1 for r in block['regions']} & set(fact['physical_pages']):
                    continue
                offset = 0
                while (offset := block['text'].casefold().find(anchor.casefold(), offset)) != -1:
                    spans.append(dict(file_id=document['file']['file_id'],
                                      start=block['start_offset'] + offset,
                                      end=block['start_offset'] + offset + len(anchor)))
                    offset += len(anchor)
            anchors.append(dict(anchor=anchor, spans=spans))
        result[identity] = dict(fact=fact, anchors=anchors,
                               fully_mapped=all(a['spans'] for a in anchors))
    return result


LABELS = locations()


def overlaps(chunk, span):
    return chunk['file_id'] == span['file_id'] and chunk['start_offset'] < span['end'] and span['start'] < chunk['end_offset']


def relevant(chunk, facts):
    return any(overlaps(chunk, s) for f in facts for a in LABELS[f]['anchors'] for s in a['spans'])


def retrieval_scores(ids, facts):
    if not facts:
        return None
    selected = [CHUNKS[i] for i in ids[:5]]
    binary = [int(relevant(c, facts)) for c in selected]
    covered = sum(all(any(c['file_id'] == s['file_id'] and c['start_offset'] <= s['start'] and c['end_offset'] >= s['end']
                          for s in a['spans'] for c in selected) for a in LABELS[f]['anchors']) for f in facts)
    ideal_count = min(5, sum(relevant(c, facts) for c in CHUNKS.values()))
    ideal = sum(1 / math.log2(i + 2) for i in range(ideal_count))
    return {'Recall@K': covered / len(facts), 'Precision@K': sum(binary) / 5,
            'Hit Rate@K': int(any(binary)), 'MRR': next((1 / (i + 1) for i, b in enumerate(binary) if b), 0),
            'NDCG@K': sum(b / math.log2(i + 2) for i, b in enumerate(binary)) / ideal if ideal else 0,
            'covered_fact_anchors': covered, 'gold_facts': len(facts), 'selected_ids': ids[:5],
            'binary_relevance': binary, 'ideal_relevant_children_at_5': ideal_count}


def percentile(values, fraction):
    values = sorted(values)
    position = (len(values) - 1) * fraction
    lower = int(position)
    return values[lower] + (values[min(lower + 1, len(values) - 1)] - values[lower]) * (position - lower)


def distribution(values):
    return dict(n=len(values), mean=statistics.mean(values), p50=percentile(values, .5),
                p95=percentile(values, .95), unit='seconds', percentile_method='linear interpolation') if values else None


def records(directory):
    return [json.loads(line) for line in (directory / 'server-observations.jsonl').read_text().splitlines()]


def diagnostics():
    rows = []
    for pass_name, directory in [('before', ROOT), ('repair', ROOT / 'repair-1')]:
        observations = records(directory)
        for case in FROZEN['cases']:
            for arm in ['single', 'planned']:
                identity = case['id'] + '-' + arm
                answer = json.loads((directory / (identity + '.json')).read_text())
                stages = [r for r in observations if r['request'] == identity and r['kind'] == 'stage']
                result = stages[-1]['result'] if stages else None
                selected, query_scores = [], []
                if result:
                    if arm == 'single':
                        selected = [c['chunk_id'] for c in result['diagnostics']['candidates']]
                        diagnostics = [result['diagnostics']]
                    else:
                        selected = result['trace']['selected_ids']
                        diagnostics = [r['result']['diagnostics'] for r in result['trace']['runs']]
                    for i, diag in enumerate(diagnostics):
                        # These stages have incomplete anchor labels. Preserve distinct
                        # route/fusion/rerank scores; do not call any one of them final.
                        for stage in ['vector_matches', 'bm25_matches', 'fused_matches']:
                            ids = [c['chunk_id'] for c in diag[stage]]
                            query_scores.append(dict(query_index=i, stage=stage, scores=retrieval_scores(ids, case['expected_fact_ids'])))
                        rerank = diag.get('rerank')
                        if rerank:
                            query_scores.append(dict(query_index=i, stage='reranked',
                                scores=retrieval_scores([c['chunk_id'] for c in rerank['matches']], case['expected_fact_ids'])))
                rows.append(dict(pass_name=pass_name, case_id=case['id'], arm=arm, status=answer['status'],
                    artifact=str((directory / (identity + '.json')).relative_to(ROOT)),
                    scores=retrieval_scores(selected, case['expected_fact_ids']), per_query=query_scores))
    assert json.loads((ROOT / 'anchor-labels.json').read_text()) == LABELS
    write('retrieval-diagnostics-v2.json', dict(K=5, method='Frozen anchor spans; case-folded literal matches on annotated pages. All anchors required for fact recall; any span touch for binary child relevance. Non-exhaustive labels; no semantic correctness inference. Missing anchors count as misses, not removed from the denominator. No-gold questions are excluded. Zero IDCG has NDCG 0 by convention.', rows=rows))


if __name__ == '__main__':
    diagnostics()
