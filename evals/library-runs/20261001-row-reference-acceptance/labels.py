"""Freeze source-anchor diagnostics before answers; semantic support is reviewed separately."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def locations(facts, documents):
    labels = {}
    for identity, fact in facts.items():
        document = next(d for d in documents if d['file']['file_name'] == fact['file'])
        anchors = []
        for anchor in fact['anchors']:
            spans = []
            for block in document['extraction']['blocks']:
                if not any(r['page_index'] + 1 in fact['physical_pages'] for r in block['regions']):
                    continue
                start = 0
                while (start := block['text'].casefold().find(anchor.casefold(), start)) >= 0:
                    spans.append(dict(file_id=document['file']['file_id'], start=block['start_offset'] + start,
                                      end=block['start_offset'] + start + len(anchor)))
                    start += len(anchor)
            anchors.append(dict(anchor=anchor, spans=spans))
        labels[identity] = dict(fact=fact, anchors=anchors, fully_mapped=all(a['spans'] for a in anchors))
    return labels


def covered(units, label):
    return all(any(u['file_id'] == s['file_id'] and u['start_offset'] <= s['start'] and u['end_offset'] >= s['end']
                   for u in units for s in a['spans']) for a in label['anchors'])


def scores(ids, facts, chunks, labels, k=5):
    if not facts:
        return None
    relevant = {identity for identity, chunk in chunks.items() if any(covered([chunk], labels[f]) for f in facts)}
    binary = [int(identity in relevant) for identity in ids[:k]]
    ideal = sum(1 / math.log2(i + 2) for i in range(min(k, len(relevant))))
    selected = [chunks[i] for i in ids[:k]]
    return {'Recall@K': sum(binary) / len(relevant) if relevant else None,
            'Precision@K': sum(binary) / k, 'Hit Rate@K': int(any(binary)),
            'MRR': next((1 / (i + 1) for i, b in enumerate(binary) if b), 0),
            'NDCG@K': sum(b / math.log2(i + 2) for i, b in enumerate(binary)) / ideal if ideal else None,
            'relevant_child_count': len(relevant), 'top_ids': ids[:k], 'binary_relevance': binary,
            'fact_anchor_recall': sum(covered(selected, labels[f]) for f in facts) / len(facts)}


if __name__ == '__main__':
    target = ROOT / 'frozen-labels.json'
    assert not target.exists()
    frozen = json.loads((ROOT / 'frozen-cases.json').read_text())
    snapshot = json.loads((ROOT / 'index-snapshot.json').read_text())
    labels = locations(frozen['facts'], snapshot['files'])
    target.write_text(json.dumps(labels, indent=2) + '\n')
    print(f'{sum(l["fully_mapped"] for l in labels.values())}/{len(labels)} reference points mapped. Unmapped anchors remain visible.')
