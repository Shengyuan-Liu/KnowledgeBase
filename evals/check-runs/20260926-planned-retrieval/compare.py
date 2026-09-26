"""Scoped offline retrieval comparison; no planner, LLM judge or provider API."""
from hashlib import sha256
import json
import math
from pathlib import Path
from statistics import mean
from tempfile import TemporaryDirectory
from time import perf_counter
from unittest.mock import Mock
import sys

from knowledgebase.config import RetrievalOptions
from knowledgebase.rag.context import build_context
from knowledgebase.rag.planning import AnswerRequirement, PlannedQuery, RetrievalPlan, direct_plan
from knowledgebase.rag.planned_retrieval import retrieve_plan
from knowledgebase.rag.retrieval import retrieve_evidence
from knowledgebase.schemas import Chunk
from knowledgebase.storage.operations import create_file, save_chunks, update_file_status
from knowledgebase.storage.runtime import open_storage

DIRECTORY = Path(__file__).parent
fixture_path = DIRECTORY / 'fixture.json'
fixture = json.loads(fixture_path.read_text())
output = DIRECTORY / sys.argv[1]
assert not output.exists(), 'Use a new output path.'
rows = []
K = 2

def metrics(ranking, chunks, gold):
    binary = [int(identity in gold) for identity in ranking[:K]]
    count = sum(binary)
    ideal = sum(1 / math.log2(i + 2) for i in range(min(K, len(gold))))
    covered = {chunk.chunk.file_id for chunk in chunks
               if chunk.chunk.file_id in gold and chunk.chunk.start_offset == 0
               and chunk.chunk.end_offset == len(next(d['text'] for d in fixture['corpus'] if d['id'] == chunk.chunk.file_id))}
    return {'Recall@K': count / len(gold), 'Precision@K': count / K,
            'Hit Rate@K': float(count > 0), 'MRR': next((1/(i+1) for i, bit in enumerate(binary) if bit), 0.0),
            'NDCG@K': sum(bit/math.log2(i+2) for i, bit in enumerate(binary))/ideal,
            'Final evidence coverage': len(covered)/len(gold)}

with TemporaryDirectory(prefix='kb-planned-comparison-') as directory:
    with open_storage(Path(directory)) as (sessions, store):
        with sessions.begin() as session:
            for document in fixture['corpus']:
                identity, text = document['id'], document['text']
                create_file(session, identity, document['name'])
                chunk = Chunk(chunk_id=f'{identity}:0', file_id=identity, index=0, text=text, start_offset=0, end_offset=len(text))
                save_chunks(session, [chunk])
                store.upsert_chunks([chunk], [document['vector']])
                update_file_status(session, identity, 'ready')
        embeddings = Mock()
        embeddings.embed_query.side_effect = lambda query: fixture['query_vectors'][query]
        for strategy in ['vector', 'hybrid']:
            options = RetrievalOptions(strategy=strategy, candidate_limit=2, rerank_enabled=False)
            for case in fixture['cases']:
                plan = direct_plan(case['question']) if case['queries'] is None else RetrievalPlan(
                    original_question=case['question'], resolved_question=case['question'], route='decomposed',
                    requirements=[AnswerRequirement(requirement_id=identity, description=identity)
                                  for identity in dict.fromkeys(r for q in case['queries'] for r in q['requirement_ids'])],
                    queries=[PlannedQuery.model_validate(q) for q in case['queries']],
                )
                pair = {'case_id': case['id'], 'strategy': strategy, 'question': case['question'],
                        'gold_spans': [{'file_id': d['id'], 'start': 0, 'end': len(d['text'])}
                                       for d in fixture['corpus'] if d['id'] in case['gold']],
                        'options': options.model_dump(), 'budget': case['budget']}
                with sessions() as session:
                    for variant in ['single', 'planned']:
                        start = perf_counter()
                        if variant == 'single':
                            evidence = retrieve_evidence(case['question'], session, embeddings, store, top_k=K,
                                                         evidence_max_tokens=case['budget'], retrieval_options=options)
                            trace = None
                        else:
                            result = retrieve_plan(plan, session, embeddings, store, top_k=K,
                                                   evidence_max_tokens=case['budget'], retrieval_options=options)
                            evidence, trace = result.evidence, result.trace.model_dump(mode='json')
                        elapsed = perf_counter() - start
                        ranking = [c.file_id for c in evidence.diagnostics.candidates]
                        pair[variant] = {'metrics': metrics(ranking, evidence.chunks, case['gold']),
                                         'ranked_file_ids': ranking, 'retrieval_seconds': elapsed,
                                         'evidence': evidence.model_dump(mode='json'), 'context': build_context(evidence.chunks), 'trace': trace}
                pair['deltas'] = {key: pair['planned']['metrics'][key] - value for key, value in pair['single']['metrics'].items()}
                rows.append(pair)
report = {'fixture_sha256': sha256(fixture_path.read_bytes()).hexdigest(), 'K': K,
          'protocol': 'Complete binary labels over four canonical source spans, one child per span. Scores measure selected candidate order before packing; denominator K even for fewer hits. MRR cutoff K. NDCG binary gain, log2 discount. Final coverage counts whole gold spans in actual context. Macro means within each strategy/variant. No generation or semantic reviewer.',
          'controls': 'Same corpus, questions, labels, index, top_k=2, budgets, tokenizer and retrieval options for each pair. Only supplied independent plan queries/merge/representative selection differ. Hand-authored fixed vectors and plans; not live quality evidence. Sequential concurrency one; cold tokenizer on first pair; no provider/model loading or queue. Single pass, baseline always first; latency comparisons are not causal.',
          'cases': rows,
          'aggregates': {strategy: {variant: {metric: mean(r[variant]['metrics'][metric] for r in rows if r['strategy'] == strategy)
                        for metric in rows[0]['single']['metrics']} for variant in ['single', 'planned']} for strategy in ['vector', 'hybrid']}}
output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report['aggregates'], indent=2))
