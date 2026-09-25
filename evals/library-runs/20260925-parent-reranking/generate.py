"""One four-answer acceptance probe after completed retrieval coverage verification."""
import asyncio
import json
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace
from openai import AsyncOpenAI
from evals.automatic import RecordedResponses
from evals.evaluate import append_jsonl, digest, git_state, read_jsonl, timestamp, write_json
from knowledgebase.config import Settings
from knowledgebase.providers.llm import StreamingLLMClient
from knowledgebase.rag.generation import ANSWER_INSTRUCTIONS, _answer_messages
from knowledgebase.schemas import RetrievedChunk, StructuredChunk

DIR=Path(__file__).parent
BASE=DIR.parent/'20260925T002400Z-semantic-acceptance'
VARIANTS=('semantic-child-4096','semantic-parent-6144')
IDS=('msds-working-enrollment','msds-cpt-source-context')


def chunks_for(row):
    return [RetrievedChunk(chunk=StructuredChunk(**{**s,'index':0}),file_name=s['file_name'],distance=s['distance'],
        fusion=s.get('fusion'),rerank=s.get('rerank'),parent_id=s['parent_id'],matched_child_ids=s['matched_child_ids']) for s in row['sources']]


async def main():
    assert not (DIR/'generation-run.json').exists()
    cases={c['id']:c for c in json.loads((BASE/'cases.json').read_text())}
    rows={v:{r['case_id']:r for r in read_jsonl(DIR/f'{v}.jsonl')} for v in VARIANTS}
    for identity,control in rows[VARIANTS[0]].items():
        new=rows[VARIANTS[1]][identity]
        assert control['status']==new['status']=='ok'
        if control['coverage']['annotated_char_recall'] is not None:
            assert new['coverage']['annotated_char_recall']>=control['coverage']['annotated_char_recall']
    for identity in IDS:
        assert rows[VARIANTS[1]][identity]['coverage']['annotated_char_recall']==1
    original_calls={c['case_id']:c for c in read_jsonl(BASE/'semantic/calls.jsonl') if c['stage']=='generation'}
    for identity in IDS:
        assert _answer_messages(cases[identity]['question'],chunks_for(rows[VARIANTS[0]][identity]))[1]==original_calls[identity]['messages'][1]
    frozen=json.loads((DIR.parent/'20260925-generation-citations/freeze.json').read_text())
    settings=Settings(**frozen['config'])
    assert digest(ANSWER_INSTRUCTIONS.encode())==frozen['new_prompt_sha256']
    meta={'started_at':timestamp(),'git':git_state(),'status':'running','scope':'Four generation-only requests, two known failed questions; unchanged prompt. No new embeddings, retrieval, judge or ingestion.',
        'model':settings.answer_model,'concurrency':1,'timeout_seconds':settings.eval_timeout_seconds,'max_retries':0,'case_ids':IDS,
        'prompt_sha256':digest(ANSWER_INSTRUCTIONS.encode()),'inputs_sha256':{v:digest((DIR/f'{v}.jsonl').read_bytes()) for v in VARIANTS},
        'review_protocol':'Codex manual claim/expected-point evidence review of all four outputs; familiar cases, not independent human evaluation.'}
    write_json(DIR/'generation-run.json',meta)
    calls=[];start=perf_counter()
    async with AsyncOpenAI(api_key=settings.openai_api_key,base_url=settings.openai_base_url,timeout=settings.eval_timeout_seconds,max_retries=0) as sdk:
        adapter=RecordedResponses(sdk,calls);llm=StreamingLLMClient(SimpleNamespace(responses=adapter),settings.answer_model)
        for identity in IDS:
            for variant in VARIANTS:
                trace=rows[variant][identity]
                row={'case_id':identity,'variant':variant,'sources':trace['sources'],'coverage':trace['coverage'],'answer':'','status':'error'}
                adapter.case_id=identity
                try:
                    async for delta in llm.stream(_answer_messages(cases[identity]['question'],chunks_for(trace))): row['answer']+=delta
                    row['status']='ok'
                except Exception as error:
                    row['error_type']=type(error).__name__
                call=calls[-1];call['variant']=variant
                row.update(generation_seconds=call.get('seconds'),generation_first_delta_seconds=next((d['seconds'] for d in call.get('deltas',[]) if d['delta']),None))
                append_jsonl(DIR/'generation-answers.jsonl',row);append_jsonl(DIR/'generation-calls.jsonl',call)
                print(identity,variant,row['status'],flush=True)
    meta.update(status='completed' if all(c['status']=='ok' for c in calls) else 'failed',finished_at=timestamp(),wall_seconds=perf_counter()-start)
    write_json(DIR/'generation-run.json',meta)


if __name__=='__main__':asyncio.run(main())
