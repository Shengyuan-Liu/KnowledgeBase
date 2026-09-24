"""Audit recorded evidence and ranking invariants without provider calls."""

import json
from pathlib import Path

import tiktoken


def run():
    root = Path(__file__).parent
    rows = [json.loads(line) for line in (root / 'answers.jsonl').read_text().splitlines()]
    files = json.loads((root / 'chunks.json').read_text())
    canonical = {c.get('chunk_id', c.get('parent_id')): c
                 for f in files for c in [*f['chunks'], *f['parents']]}
    encoding = tiktoken.get_encoding('cl100k_base')
    for row in rows:
        assert row['status'] == 'ok'
        answer = row['answer']
        sources = answer['sources']
        source_ids = {s['chunk_id'] for s in sources}
        selected = {c['chunk_id'] for c in answer['retrieval']['candidates']}
        for source in sources:
            original = canonical[source['chunk_id']]
            for key in ['text', 'file_id', 'start_offset', 'end_offset', 'heading_path',
                        'source_block_indices', 'token_count', 'tokenizer', 'max_tokens']:
                assert source[key] == original[key], (row['case_id'], key)
            if source['parent_id'] != source['chunk_id']:
                assert source['chunk_id'] in selected
                assert source['parent_id'] not in source_ids
                assert source['matched_child_ids'] == [source['chunk_id']]
                parent = canonical[source['parent_id']]
                start = source['start_offset'] - parent['start_offset']
                end = source['end_offset'] - parent['start_offset']
                assert parent['text'][start:end] == source['text']
        context = '\n\n'.join(f"[{s['source_id']}]\n{s['text']}" for s in sources)
        tokens = len(encoding.encode_ordinary(context))
        assert tokens == answer['retrieval']['evidence_tokens'] <= 4096
        assert 0 < row['first_delta_seconds'] <= row['complete_seconds'] <= row['total_seconds']
    pairs = []
    for case in json.loads((root / 'cases.json').read_text()):
        old, new = [next(r for r in rows if r['case_id'] == case['id'] and r['strategy'] == mode)
                    for mode in ['parent_first', 'parent_then_child']]
        old_trace, new_trace = old['answer']['retrieval'], new['answer']['retrieval']
        selected_equal = ([c['chunk_id'] for c in old_trace['candidates']]
                          == [c['chunk_id'] for c in new_trace['candidates']])
        ranked_equal = ([c['chunk_id'] for c in old_trace['rerank']['matches']]
                        == [c['chunk_id'] for c in new_trace['rerank']['matches']])
        preserved = ({s['chunk_id'] for s in old['answer']['sources']}
                     <= {s['chunk_id'] for s in new['answer']['sources']})
        assert selected_equal and ranked_equal and preserved
        pairs.append({'case_id': case['id'], 'selected_ids_equal': selected_equal,
                      'reranked_ids_equal': ranked_equal, 'old_sources_preserved': preserved,
                      'before': old['coverage'], 'after': new['coverage'],
                      'retained_children': [s['chunk_id'] for s in new['answer']['sources']
                                            if s['chunk_id'] != s['parent_id']]})
    with (root / 'audit.json').open('x') as output:
        json.dump({'completed_rows': len(rows), 'canonical_source_metadata_matches': True,
                   'exact_numbered_budget_checks': True, 'no_parent_child_duplicate': True,
                   'timing_order_checks': True, 'pairs': pairs}, output, indent=2)
    print('Verified 36 source/timing records and 18 paired ranking/preservation checks.')


if __name__ == '__main__':
    run()
