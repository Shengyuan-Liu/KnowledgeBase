"""Compare parent scoring and evidence budgets over frozen route observations."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import platform
from statistics import mean
from time import perf_counter
from types import SimpleNamespace

from evals import metrics
from evals.evaluate import append_jsonl, digest, git_state, read_jsonl, timestamp, write_json
from knowledgebase.config import RetrievalOptions
from knowledgebase.providers.reranker import RerankerClient
from knowledgebase.schemas import RelevanceScore, VectorMatch
from knowledgebase.services.chat import _retrieve_evidence
from knowledgebase.storage.database import build_engine, build_session_factory

DIR = Path(__file__).parent
BASE = DIR.parent/'20260925T002400Z-semantic-acceptance'
spec = importlib.util.spec_from_file_location('analyze', BASE/'analyze.py')
analyze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyze)


class SavedScores:
    def __init__(self, trace):
        self.trace = trace
        for key in ('model', 'model_revision', 'device', 'batch_size', 'max_pair_tokens'):
            setattr(self, key, trace[key])

    def score(self, question, candidates):
        assert question == self.trace['question']
        assert [c.model_dump(exclude={'scoring_parent_id'}) for c in candidates] == self.trace['candidates']
        by = {m['chunk_id']: m['rerank_score'] for m in self.trace['matches']}
        return [RelevanceScore(chunk_id=c.chunk_id, score=by[c.chunk_id]) for c in candidates]


class CachedLocalScores:
    def __init__(self, client):
        self.client, self.cache = client, {}
        for key in ('model', 'model_revision', 'device', 'batch_size', 'max_pair_tokens'):
            setattr(self, key, getattr(client, key))

    def score(self, question, candidates):
        key = digest(json.dumps([question, [c.model_dump() for c in candidates]], sort_keys=True).encode())
        self.last_cached = key in self.cache
        if not self.last_cached:
            self.cache[key] = self.client.score(question, candidates)
        return self.cache[key]


def summarize(rows, path, runtime):
    eligible = [r for r in rows if r['status'] == 'ok' and r['coverage']['annotated_char_recall'] is not None]
    inventory = {key: metrics.missing('No generation, provider calls, ingestion or lifecycle exercised in this frozen-route retrieval replay.', False)
                 for key in json.loads(Path('evals/check-runs/20260924-judge-calibration/backend-6.json').read_text())['metric_inventory']}
    for key in ('recall_at_k','precision_at_k','hit_rate_at_k','mrr_at_k','ndcg_at_k'):
        ranked = [r['stages']['supplied_evidence']['fixed_block_ranking'][key] for r in eligible]
        inventory[key] = metrics.measured(mean(ranked), 'fraction', len(ranked),
            'K=5 unique frozen parser blocks induced by final evidence order; binary gold-overlap proxy, incomplete relevance labels; source order within region. Not native child ranking.', path)
    inventory['final_evidence_coverage'] = metrics.measured({
        'annotated_char_recall':mean(r['coverage']['annotated_char_recall'] for r in eligible),
        'full_evidence_recall':mean(r['coverage']['full_evidence_recall'] for r in eligible)},
        'fraction',len(eligible),'Macro-average annotated source spans; final actually supplied exact evidence.',path)
    inventory['stage_latency'] = {'status':'measured','value':{
        'replay_retrieval':metrics.timing([r['seconds'] for r in rows if r['status']=='ok']),
        'reranking':metrics.timing([r['retrieval']['rerank_seconds'] for r in rows if r['status']=='ok']),
        'packing':metrics.timing([r['retrieval']['packing_seconds'] for r in rows if r['status']=='ok'])},
        'method':'Single sequential local replay, no embedding; excludes separate model loading. Cached score rows are not inference latency. P50 median/P95 nearest rank.', 'artifact':path}
    inventory['reliability'] = metrics.measured({'success':sum(r['status']=='ok' for r in rows),'error':sum(r['status']!='ok' for r in rows),'timeout':0,'retries':0},'requests',len(rows),'Local replay only; all planned queries retained.',path)
    inventory['concurrency_and_throughput'] = metrics.measured({'concurrency':1,'wall_seconds':runtime,'successful_requests_per_second':sum(r['status']=='ok' for r in rows)/runtime},'requests/second',len(rows),'Local replay including analysis/logging, mixed cached/inference states; not service capacity.',path)
    return {'metric_inventory':inventory,'limitations':['All cases are development cases; no independent human labels.', 'Saved vector routes; BM25/RRF recomputed; no new embedding or ingestion.', 'Parent/child scoring use different pair/input caps; budgets compared separately.', 'Single pass; cached scores excluded from inference speed claims.'], 'per_case_artifact':path}


def main():
    assert not (DIR/'run.json').exists(), 'Use a new directory for another attempt.'
    cases=json.loads((BASE/'cases.json').read_text()); blocks=json.loads((BASE/'blocks.json').read_text())
    meta={'started_at':timestamp(),'git':git_state(),'platform':platform.platform(),'status':'running','concurrency':1,
        'cases_sha256':digest((BASE/'cases.json').read_bytes()),'corpus_sha256':digest((BASE/'corpus.json').read_bytes()),
        'route_candidate_limit':20,'rerank_candidate_limit':20,'top_k':5,'units':['child','parent'],'budgets':[4096,6144],
        'baseline_sha256':{f'{strategy}/{name}':digest((BASE/strategy/name).read_bytes()) for strategy in ('parent_child','semantic') for name in ('answers.jsonl','chunks.json','parents.json')},
        'command':'HF_HUB_OFFLINE=1 uv run python -m evals.library-runs.20260925-parent-reranking.retrieve'}
    write_json(DIR/'run.json',meta)
    start=perf_counter(); client=RerankerClient('BAAI/bge-reranker-v2-m3',max_pair_tokens=2048)
    meta.update(model_loading_seconds=perf_counter()-start,model=client.model,model_revision=client.model_revision,device=client.device,batch_size=client.batch_size)
    for strategy in ('parent_child','semantic'):
        originals={a['case_id']:a for a in read_jsonl(BASE/strategy/'answers.jsonl')}
        chunks=json.loads((BASE/strategy/'chunks.json').read_text())
        engine=build_engine(f'sqlite:///data/evals/20260925T002400Z-semantic-acceptance/evals/{strategy}/knowledgebase.db')
        sessions=build_session_factory(engine)
        local=CachedLocalScores(client)
        for unit in ('child','parent'):
            for budget in (4096,6144):
                label=f'{strategy}-{unit}-{budget}'; rows=[]; started=perf_counter()
                for case in cases:
                    old=originals[case['id']]
                    scorer=SavedScores(old['retrieval']['rerank']) if unit=='child' else local
                    vector=SimpleNamespace(search=lambda *args, **kwargs: [VectorMatch(**m) for m in old['retrieval']['vector_matches']])
                    options=RetrievalOptions(rerank_enabled=True,rerank_unit=unit,rerank_max_input_tokens=32768 if unit=='parent' else 16384)
                    t=perf_counter(); row={'case_id':case['id'],'status':'error','variant':label}
                    try:
                        _,sources,trace=_retrieve_evidence(case['question'],sessions,SimpleNamespace(embed_query=lambda q:[]),vector,5,budget,'cl100k_base',options,scorer)
                        trace.embedding_seconds=None
                        row.update(status='ok',sources=[s.model_dump(mode='json') for s in sources],retrieval=trace.model_dump(mode='json'),seconds=perf_counter()-t,
                            scores_origin='historical' if unit=='child' else 'same-run-cache' if local.last_cached else 'local-inference')
                        row['coverage']=analyze.retrieval_metrics(case,row['sources'])
                        row['stages']=analyze.ranking_trace(case,row,chunks,blocks)['stages']
                        scoring={c.chunk_id:c for c in trace.rerank.candidates}
                        regions=[]
                        by={c['chunk_id']:c for c in chunks}
                        parents={p['parent_id']:p for p in json.loads((BASE/strategy/'parents.json').read_text())}
                        for match in trace.rerank.selected:
                            candidate=scoring[match.chunk_id]
                            regions.append(parents[candidate.scoring_parent_id] if candidate.scoring_parent_id else by[match.chunk_id])
                        row['stages']['scored_regions_top5']={'source_span_coverage':analyze.retrieval_metrics(case,regions), 'fixed_block_ranking':analyze.fixed_block_ranking(case,regions,blocks)}
                        if unit=='child' and budget==4096:
                            def signature(items):
                                return [(s['chunk_id'],s['text'],s['start_offset'],s['end_offset'],s['matched_child_ids']) for s in items]
                            assert signature(row['sources'])==signature(old['sources']), 'Default evidence changed.'
                    except Exception as error:
                        row.update(status='error',error_type=type(error).__name__,error=str(error),seconds=perf_counter()-t)
                    rows.append(row);append_jsonl(DIR/f'{label}.jsonl',row)
                write_json(DIR/f'{label}-summary.json',summarize(rows,f'{label}.jsonl',perf_counter()-started))
                print(label,[(r['case_id'],r['status'],r.get('coverage',{}).get('annotated_char_recall')) for r in rows if r['status']!='ok' or r['case_id'] in ('msds-working-enrollment','msds-cpt-source-context')],flush=True)
        engine.dispose()
    meta.update(status='completed',finished_at=timestamp())
    write_json(DIR/'run.json',meta)


if __name__=='__main__':
    main()
