"""Frozen source-span comparison: prior direct route versus bounded dependencies."""
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
    binary = [int(identity in gold) for identity in ranking[:K]]
    ideal = sum(1 / math.log2(i + 2) for i in range(min(K, len(gold))))
    covered = {s.file_id for s in sources if s.file_id in gold and s.start_offset == 0
               and s.end_offset == len(next(d['text'] for d in fixture['corpus'] if d['id'] == s.file_id))}
    return {'Recall@K': sum(binary) / len(gold), 'Precision@K': sum(binary) / K,
            'Hit Rate@K': float(any(binary)), 'MRR': next((1/(i+1) for i, bit in enumerate(binary) if bit), 0.0),
            'NDCG@K': sum(bit/math.log2(i+2) for i, bit in enumerate(binary))/ideal,
            'Final evidence coverage': len(covered)/len(gold)}


with TemporaryDirectory(prefix='kb-dependent-comparison-') as directory:
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
        options = RetrievalOptions(strategy='vector', candidate_limit=1, rerank_enabled=False)
        for case in fixture['cases']:
            pair = {'case_id': case['id'], 'question': case['question'],
                'gold_spans': [{'file_id': d['id'], 'start': 0, 'end': len(d['text'])}
                               for d in fixture['corpus'] if d['id'] in case['gold']],
                'options': options.model_dump(), 'budget': case['budget'], 'file_ids': case['file_ids']}
            for variant in ['before_direct', 'after_dependent']:
                def respond(**kwargs):
                    if 'text' not in kwargs:
                        text = 'Offline answer placeholder. [1]'
                    elif kwargs['text']['format']['name'] == 'retrieval_plan':
                        text = json.dumps(fixture['direct'] if variant == 'before_direct' else fixture['plans'][case['plan']])
                    else:
                        payload = json.loads(kwargs['input'][-1]['content'])
                        decisions = []
                        for item in payload['pending_queries']:
                            target = fixture['targets'][item['query_id']]
                            excerpt = next(e for e in item['evidence'] if target in e['text'])
                            decisions.append({'query_id': item['query_id'], 'status': 'resolved', 'target': target,
                                'references': [{'evidence_id': excerpt['evidence_id'], 'quote': excerpt['text']}]})
                        text = json.dumps({'decisions': decisions})
                    return SimpleNamespace(output_text=text, status='completed', model='offline-fixture', id='offline', usage=None)
                sdk.responses.create.side_effect = respond
                sdk.responses.create.reset_mock()
                embeddings.embed_query.reset_mock()
                start = perf_counter()
                result = answer_in_conversation(case['question'], sessions, embeddings, store, llm,
                    top_k=K, evidence_max_tokens=case['budget'], retrieval_options=options,
                    planner_client=planner, file_ids=case['file_ids'])
                elapsed = perf_counter() - start
                ranking = [c.file_id for c in result.retrieval.candidates]
                with sessions() as session:
                    assert get_conversation_detail(session, result.conversation_id).messages[-1].retrieval == result.retrieval
                pair[variant] = {'metrics': metrics(ranking, result.sources, case['gold']),
                    'ranked_file_ids': ranking, 'service_seconds': elapsed,
                    'answer': result.model_dump(mode='json'), 'query_executions': embeddings.embed_query.call_count,
                    'model_inputs': [c.kwargs for c in sdk.responses.create.call_args_list]}
            pair['deltas'] = {key: pair['after_dependent']['metrics'][key] - value for key, value in pair['before_direct']['metrics'].items()}
            rows.append(pair)
report = {'fixture_sha256': sha256(fixture_path.read_bytes()).hexdigest(), 'K': K,
    'protocol': 'Complete binary labels over five canonical spans, one child per span. Scope-only case labels one allowed span. Scores measure selected candidate order before packing; denominator K even for fewer hits. MRR cutoff K. NDCG binary gain, log2 discount. Final coverage counts whole gold spans in actual context. Macro mean across four cases. No semantic answer scoring.',
    'controls': 'Identical corpus/questions/labels/vectors/top_k=3/budgets/options within each pair. Before replays the predecessor direct decision for dependent questions through the existing direct path; after replays a frozen dependency plan and literal target choices. Both use current code and prompt metadata, so this is a controller ablation, not a live model or old-binary comparison. Sequential concurrency one; no provider/model loading or queue. Cold tokenizer possible on first pair, baseline first, one pass. Mock timings do not establish production latency.',
    'cases': rows,
    'aggregates': {variant: {metric: mean(r[variant]['metrics'][metric] for r in rows)
        for metric in rows[0]['before_direct']['metrics']} for variant in ['before_direct','after_dependent']}}
output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report['aggregates'], indent=2))
