"""Check parent scoring on the same two failures with the original candidate routes."""
import json
from pathlib import Path
from time import perf_counter
from evals.evaluate import git_state, timestamp, write_json
from knowledgebase.schemas import RerankCandidate
from knowledgebase.rag.reranking import rerank
from knowledgebase.providers.reranker import RerankerClient

DIR = Path(__file__).parent
BASE = DIR.parent/'20260925T002400Z-semantic-acceptance'
if __name__ == '__main__':
    assert not (DIR/'parent-results.json').exists()
    start=perf_counter()
    metadata={'started_at':timestamp(),'git':git_state(),'scope':'Two observed failures; local whole-parent scoring over original route candidates, no provider calls. Exploratory, not acceptance.', 'concurrency':1}
    chunks={c['chunk_id']:c for c in json.loads((BASE/'semantic/chunks.json').read_text())}
    parents={p['parent_id']:p for p in json.loads((BASE/'semantic/parents.json').read_text())}
    cases={c['id']:c for c in json.loads((BASE/'cases.json').read_text())}
    loading=perf_counter()
    client=RerankerClient('BAAI/bge-reranker-v2-m3',max_pair_tokens=2048)
    metadata.update(model=client.model,revision=client.model_revision,device=client.device,model_loading_seconds=perf_counter()-loading)
    results=[]
    for old in json.loads((DIR/'results.json').read_text()):
        seen=set(); candidates=[]
        for m in old['original_retrieval']['fused_matches']:
            c=chunks[m['chunk_id']]; p=parents[c['parent_id']]
            if p['parent_id'] in seen: continue
            seen.add(p['parent_id'])
            candidates.append(RerankCandidate(**m,text=p['text'],heading_path=json.loads(p['heading_path'])))
        t=perf_counter()
        scored=rerank(cases[old['case_id']]['question'],candidates,client,top_k=5,candidate_limit=20,max_input_tokens=32768)
        results.append({'case_id':old['case_id'],'rerank':scored.model_dump(),'rerank_seconds':perf_counter()-t})
        print(old['case_id'],scored.input_tokens,flush=True)
        for m in scored.matches[:5]:
            c=chunks[m.chunk_id];p=parents[c['parent_id']]
            print(m.rerank_rank,p['file_name'],p['start_offset'],p['end_offset'],round(m.rerank_score,3),flush=True)
    write_json(DIR/'parent-results.json',results)
    metadata.update(finished_at=timestamp(),seconds=perf_counter()-start,status='completed')
    write_json(DIR/'parent-run.json',metadata)
