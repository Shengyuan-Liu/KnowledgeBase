"""Record where the indexed lecture facts disappeared, without running retrieval again."""
import json
from pathlib import Path

from labels import covered

ROOT = Path(__file__).resolve().parent

if __name__ == '__main__':
    answer = json.loads((ROOT / 'lecture-bag-words-planned.json').read_text())
    snapshot = json.loads((ROOT / 'index-snapshot.json').read_text())
    labels = json.loads((ROOT / 'frozen-labels.json').read_text())
    document = next(d for d in snapshot['files'] if d['file']['file_name'] == 'ml-lecture.pdf')
    planning = answer['answer']['retrieval']['planning']
    rows = []
    for fact in ['topic_documents', 'topic_words']:
        children = [c for c in document['chunks'] if covered([c], labels[fact])]
        ids = {c['chunk_id'] for c in children}
        parents = [p for p in document['parents'] if p['parent_id'] in {c['parent_id'] for c in children}]
        queries = []
        for run in planning['trace']['runs']:
            diagnostics = run['result']['diagnostics']
            ranks = {stage: [dict(rank=i+1, chunk_id=m['chunk_id']) for i, m in enumerate(diagnostics[stage]) if m['chunk_id'] in ids]
                     for stage in ['vector_matches', 'bm25_matches', 'fused_matches']}
            ranks['rerank_candidates'] = [dict(rank=i+1, chunk_id=m['chunk_id']) for i, m in enumerate(diagnostics['rerank']['candidates']) if m['chunk_id'] in ids]
            queries.append(dict(round_index=run['round_index'], query=run['text'], ranks=ranks,
                                candidate_limit=diagnostics['options']['rerank_candidate_limit']))
        rows.append(dict(fact_id=fact, indexed_children=children, indexed_parents=parents, queries=queries,
                         selected_ids=list(ids & set(planning['trace']['selected_ids']))))
    record = dict(case_id='lecture-bag-words', artifact='lecture-bag-words-planned.json',
                  observed=dict(assessment_rounds=planning['assessment']['round_index'],
                                selected_page_62_source=next(s for s in answer['answer']['sources'] if s['source_id'] == 3),
                                exclusions=answer['answer']['retrieval']['excluded'],
                                unexpanded_parents=answer['answer']['retrieval']['unexpanded_parents'],
                                final_context_has_document_count='Count how many documents' in planning['assessment']['context'],
                                final_context_has_word_count='For each topic, count' in planning['assessment']['context']),
                  facts=rows,
                  conclusion='Both page-62 count bullets are correctly indexed but absent from the final context. The selected page-62 parent contains only the slide title. The document-count child is outside all candidate lists; the word-count child reaches BM25 rank 17 and fused rank 32 for both initial count queries, outside the 20-child rerank window. Supplementary queries do not recover either fact. No context-budget exclusion caused this miss.',
                  inference='The generic Learning phase heading separates the count children from the descriptive slide title. This may contribute to the ranking failure; no causal repair experiment has been run.',
                  next_scope='Address title/body retrieval association for this concrete lecture failure with scoped offline controls, then use the same frozen questions/corpus/annotations for any authorized matched live acceptance. Do not widen budgets without evidence or treat missing context as missing source facts.')
    with (ROOT / 'failure-analysis.json').open('x') as file:
        file.write(json.dumps(record, indent=2) + '\n')
    print('Preserved the lecture miss from index through candidate rankings and the final context; no replay or provider calls.')
