"""Inspect the two observed semantic misses without provider calls."""
import json
from pathlib import Path
from time import perf_counter
from evals.evaluate import git_state, read_jsonl, timestamp, write_json
from knowledgebase.schemas import ChildChunk, VectorMatch, RerankCandidate
from knowledgebase.rag.bm25 import search_bm25
from knowledgebase.rag.fusion import fuse_rrf
from knowledgebase.rag.reranking import rerank
from knowledgebase.providers.reranker import RerankerClient

DIR = Path(__file__).parent
BASE = DIR.parent / '20260925T002400Z-semantic-acceptance'
if __name__ == '__main__':
    assert not (DIR/'results.json').exists()
    start=perf_counter()
    metadata={'started_at':timestamp(),'git':git_state(),'scope':'Offline diagnosis of two observed semantic omissions; frozen vector top20, current BM25, local reranker. Not a full retrieval acceptance run.', 'concurrency':1}
    chunks=json.loads((BASE/'semantic/chunks.json').read_text())
    by={c['chunk_id']:c for c in chunks}
    corpus=[ChildChunk(**c) for c in chunks]
    cases=[c for c in json.loads((BASE/'cases.json').read_text()) if c['id'] in ('msds-working-enrollment','msds-cpt-source-context')]
    answers={a['case_id']:a for a in read_jsonl(BASE/'semantic/answers.jsonl')}
    loading=perf_counter()
    client=RerankerClient('BAAI/bge-reranker-v2-m3')
    metadata.update(model=client.model,revision=client.model_revision,device=client.device,model_loading_seconds=perf_counter()-loading)
    results=[]
    for case in cases:
        bm25=search_bm25(case['question'],corpus,top_k=40)
        fused=fuse_rrf(bm25,[VectorMatch(**m) for m in answers[case['id']]['retrieval']['vector_matches']],limit=60)
        candidates=[RerankCandidate(**m.model_dump(),text=by[m.chunk_id]['text'],heading_path=by[m.chunk_id]['heading_path']) for m in fused[:40]]
        t=perf_counter()
        scored=rerank(case['question'],candidates,client,top_k=5,candidate_limit=40,max_input_tokens=16384)
        row={'case_id':case['id'],'bm25':[m.model_dump() for m in bm25],'fused':[m.model_dump() for m in fused],'rerank':scored.model_dump(),'rerank_seconds':perf_counter()-t,
             'original_retrieval':answers[case['id']]['retrieval']}
        results.append(row)
        print(case['id'],flush=True)
        seen=set()
        for match in scored.matches:
            c=by[match.chunk_id]
            if c['parent_id'] in seen: continue
            seen.add(c['parent_id'])
            print(match.rerank_rank,c['file_name'],c['start_offset'],round(match.rerank_score,3),flush=True)
            if len(seen)==5: break
    write_json(DIR/'results.json',results)
    metadata.update(finished_at=timestamp(),seconds=perf_counter()-start,status='completed')
    inventory=json.loads(Path('evals/check-runs/20260924-judge-calibration/backend-6.json').read_text())['metric_inventory']
    metadata['metric_inventory']=inventory
    metadata['metric_scope_note']='Unit-test inventory is a template only; this diagnosis has no new answer, embedding, ingestion or provider usage. Retrieval acceptance metrics will be recorded separately on the complete feature. Raw ranks and timing are in results.json; no retrieval-quality claim from this two-case diagnostic.'
    write_json(DIR/'run.json',metadata)
