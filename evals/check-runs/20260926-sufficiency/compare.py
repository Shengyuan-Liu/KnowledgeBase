"""Replay a frozen offline corpus with and without sufficiency control."""
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
fixture_path = DIRECTORY / 'fixture.json'
fixture = json.loads(fixture_path.read_text())
output = DIRECTORY / sys.argv[1]
assert not output.exists(), 'Use a new output path.'
rows = []
K = 3


def metrics(ranking, sources, gold):
    if not gold:
        return None  # No relevance denominator on the unanswerable case.
    binary = [int(identity in gold) for identity in ranking[:K]]
    ideal = sum(1 / math.log2(i + 2) for i in range(min(K, len(gold))))
    covered = {s.file_id for s in sources if s.file_id in gold and s.start_offset == 0
               and s.end_offset == len(next(d['text'] for d in fixture['corpus'] if d['id'] == s.file_id))}
    return {'Recall@K': sum(binary) / len(gold), 'Precision@K': sum(binary) / K,
            'Hit Rate@K': float(any(binary)), 'MRR': next((1/(i+1) for i, bit in enumerate(binary) if bit), 0.0),
            'NDCG@K': sum(bit/math.log2(i+2) for i, bit in enumerate(binary))/ideal,
            'Final evidence coverage': len(covered)/len(gold)}


with TemporaryDirectory(prefix='kb-sufficiency-comparison-') as directory:
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
        llm = LLMClient(sdk, 'offline-answer')
        options = RetrievalOptions(strategy='vector', candidate_limit=1, rerank_enabled=False)
        for case in fixture['cases']:
            plan = {'route': 'decomposed', 'dependencies': [],
                'requirements': [{'requirement_id': point, 'description': fixture['points'][point]['description']} for point in case['points']],
                'queries': [{'query_id': f'initial-{i}', 'text': q, 'requirement_ids': case['points']} for i, q in enumerate(case['initial_queries'])]}
            pair = {'case': case, 'gold_spans': [{'file_id': d['id'], 'start': 0, 'end': len(d['text'])}
                                               for d in fixture['corpus'] if d['id'] in case['gold']], 'plan': plan}
            for enabled in [False, True]:
                variant = 'after' if enabled else 'before'
                def respond(**kwargs):
                    if 'text' not in kwargs:
                        text = 'Offline answer placeholder. [1]'
                    elif kwargs['text']['format']['name'] == 'retrieval_plan':
                        text = json.dumps(plan)
                    else:
                        payload = json.loads(kwargs['input'][-1]['content'])
                        requirements, queries = [], []
                        for point in case['points']:
                            gold = fixture['points'][point]['files']
                            excerpts = [e for e in payload['evidence_catalog'] if e['file_id'] in gold]
                            status = ('conflicting' if point == 'conflict' and len(excerpts) == 2 else
                                      'supported' if gold and len(excerpts) == len(gold) else 'partial' if excerpts else 'missing')
                            refs = [{'evidence_id': e['evidence_id'], 'quote': next(d['text'] for d in fixture['corpus'] if d['id'] == e['file_id'])} for e in excerpts]
                            requirements.append({'requirement_id': point, 'status': status,
                                'gap': '' if status == 'supported' else 'The requested detail is absent or unresolved.', 'references': refs})
                            if point == 'access' and status == 'missing' and payload['remaining_queries'] and payload['remaining_rounds']:
                                queries.append({'requirement_ids': [point], 'query_template': 'library access', 'target': '', 'references': []})
                        text = json.dumps({'requirements': requirements, 'queries': queries})
                    return SimpleNamespace(output_text=text, status='completed', model='offline-fixture', id='offline', usage=None)
                sdk.responses.create.side_effect = respond
                sdk.responses.create.reset_mock()
                embeddings.embed_query.reset_mock()
                planning_options = PlanningOptions(sufficiency_enabled=enabled)
                planner = PlannerClient(sdk, 'offline-planner', planning_options, 'cl100k_base')
                start = perf_counter()
                result = answer_in_conversation(case['question'], sessions, embeddings, store, llm,
                    top_k=K, evidence_max_tokens=case['budget'], retrieval_options=options,
                    planner_client=planner, planning_options=planning_options, file_ids=case['file_ids'])
                elapsed = perf_counter() - start
                ranking = [c.file_id for c in result.retrieval.candidates]
                with sessions() as session:
                    assert get_conversation_detail(session, result.conversation_id).messages[-1].retrieval == result.retrieval
                pair[variant] = {'metrics': metrics(ranking, result.sources, case['gold']),
                    'ranked_file_ids': ranking, 'service_seconds': elapsed,
                    'answer': result.model_dump(mode='json'), 'query_executions': embeddings.embed_query.call_count,
                    'model_inputs': [c.kwargs for c in sdk.responses.create.call_args_list]}
            pair['deltas'] = ({key: pair['after']['metrics'][key] - value for key, value in pair['before']['metrics'].items()}
                              if pair['before']['metrics'] else None)
            rows.append(pair)
report = {'fixture_sha256': sha256(fixture_path.read_bytes()).hexdigest(), 'K': K,
    'protocol': 'Complete binary labels over four canonical spans, one child per span; scope case labels only its allowed span. Selected candidates before packing, denominator K even for fewer hits; MRR cutoff K; NDCG binary gain/log2 discount. Final coverage requires whole gold spans. Macro average over five cases with gold; unanswerable case is excluded, never zero-filled. Mock answers are not graded.',
    'controls': 'Same frozen questions/corpus/labels/vectors/plan/K=3/budget/vector strategy/candidate_limit=1/no reranking; only PlanningOptions.sufficiency_enabled changes. Both variants use current code, not an old binary. Assessments are fixture decisions and not model quality measurements. Sequential concurrency one, baseline first, cold tokenizer possible; no provider loading/queue, no production latency claim.',
    'cases': rows,
    'aggregates': {variant: {metric: mean(r[variant]['metrics'][metric] for r in rows if r[variant]['metrics'])
        for metric in rows[0]['before']['metrics']} for variant in ['before', 'after']}}
output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report['aggregates'], indent=2))
