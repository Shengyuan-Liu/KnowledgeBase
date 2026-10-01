"""Replay the frozen stage 3a fixture through automatic planning/chat, offline."""
from hashlib import sha256
import json
import math
from pathlib import Path
from statistics import mean
from tempfile import TemporaryDirectory
from time import perf_counter
from types import SimpleNamespace
from unittest.mock import Mock
import sys

from knowledgebase.config import PlanningOptions, RetrievalOptions
from knowledgebase.providers.llm import LLMClient
from knowledgebase.providers.planner import PlannerClient
from knowledgebase.services.chat import answer_in_conversation
from knowledgebase.schemas import Chunk
from knowledgebase.storage.operations import create_file, save_chunks, update_file_status, get_conversation_detail
from knowledgebase.storage.runtime import open_storage

DIRECTORY = Path(__file__).parent
fixture_path = DIRECTORY.parent / '20260926-planned-retrieval/fixture.json'
fixture = json.loads(fixture_path.read_text())
output = DIRECTORY / sys.argv[1]
assert not output.exists(), 'Use a new output path.'
rows = []
K = 2


def metrics(ranking, sources, gold):
    binary = [int(identity in gold) for identity in ranking[:K]]
    ideal = sum(1 / math.log2(i + 2) for i in range(min(K, len(gold))))
    covered = {s.file_id for s in sources if s.file_id in gold and s.start_offset == 0
               and s.end_offset == len(next(d['text'] for d in fixture['corpus'] if d['id'] == s.file_id))}
    return {'Recall@K': sum(binary) / len(gold), 'Precision@K': sum(binary) / K,
            'Hit Rate@K': float(any(binary)), 'MRR': next((1/(i+1) for i, bit in enumerate(binary) if bit), 0.0),
            'NDCG@K': sum(bit/math.log2(i+2) for i, bit in enumerate(binary))/ideal,
            'Final evidence coverage': len(covered)/len(gold)}


with TemporaryDirectory(prefix='kb-automatic-comparison-') as directory:
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
        embeddings.bounded.return_value = embeddings
        sdk = Mock()
        sdk.with_options.return_value = sdk
        planner = PlannerClient(sdk, 'offline-planner', PlanningOptions(), 'cl100k_base')
        llm = LLMClient(sdk, 'offline-answer')
        for strategy in ['vector', 'hybrid']:
            options = RetrievalOptions(strategy=strategy, candidate_limit=2, rerank_enabled=False)
            for case in fixture['cases']:
                decision = {'route': 'direct', 'requirements': [], 'queries': []} if case['queries'] is None else {
                    'route': 'decomposed', 'requirements': [
                        {'requirement_id': identity, 'description': identity}
                        for identity in dict.fromkeys(r for q in case['queries'] for r in q['requirement_ids'])],
                    'queries': case['queries']}
                def respond(**kwargs):
                    text = json.dumps(decision) if 'text' in kwargs else 'Offline answer placeholder. [1]'
                    return SimpleNamespace(output_text=text, status='completed', model='offline-fixture', id='offline', usage=None)
                sdk.responses.create.side_effect = respond
                pair = {'case_id': case['id'], 'strategy': strategy, 'question': case['question'],
                        'gold_spans': [{'file_id': d['id'], 'start': 0, 'end': len(d['text'])}
                                       for d in fixture['corpus'] if d['id'] in case['gold']],
                        'options': options.model_dump(), 'budget': case['budget']}
                for variant in ['single', 'planned']:
                    sdk.responses.create.reset_mock()
                    start = perf_counter()
                    result = answer_in_conversation(case['question'], sessions, embeddings, store, llm,
                        top_k=K, evidence_max_tokens=case['budget'], retrieval_options=options,
                        planner_client=planner if variant == 'planned' else None)
                    elapsed = perf_counter() - start
                    ranking = [c.file_id for c in result.retrieval.candidates]
                    with sessions() as session:
                        saved = get_conversation_detail(session, result.conversation_id).messages[-1]
                        assert saved.retrieval == result.retrieval
                    pair[variant] = {'metrics': metrics(ranking, result.sources, case['gold']),
                        'ranked_file_ids': ranking, 'service_seconds': elapsed,
                        'answer': result.model_dump(mode='json'),
                        'model_inputs': [c.kwargs for c in sdk.responses.create.call_args_list]}
                pair['deltas'] = {key: pair['planned']['metrics'][key] - value for key, value in pair['single']['metrics'].items()}
                rows.append(pair)
report = {'fixture_sha256': sha256(fixture_path.read_bytes()).hexdigest(), 'K': K,
    'protocol': 'Complete binary labels over four canonical spans, one child per span. Scores measure selected candidate order before packing; denominator K even for fewer hits. MRR cutoff K. NDCG binary gain, log2 discount. Final coverage counts whole gold spans in actual context. Macro means by strategy/variant. Codex reviewed all eight pairs; no human or LLM answer review.',
    'controls': 'Identical stage 3a frozen corpus/questions/labels/vectors/plans, top_k=2 and budgets. Planner SDK responses replay hand-authored plans via real validation and chat integration. Answer output is a placeholder; no semantic quality evidence. Sequential concurrency one; no paid calls, model loading or queue. Single pass baseline first; mock timings are not production latency.',
    'cases': rows,
    'aggregates': {strategy: {variant: {metric: mean(r[variant]['metrics'][metric] for r in rows if r['strategy'] == strategy)
        for metric in rows[0]['single']['metrics']} for variant in ['single', 'planned']} for strategy in ['vector', 'hybrid']}}
previous = json.loads((fixture_path.parent / 'comparison-1-details.json').read_text())
assert report['aggregates'] == previous['aggregates'], 'Automatic integration changed frozen retrieval results.'
report['stage_3a_metric_parity'] = True
output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report['aggregates'], indent=2))
print('All metrics match the previous independent executor fixture.')
