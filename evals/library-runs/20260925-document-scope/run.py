"""Collect one frozen functional acceptance run through production services."""
import asyncio
import json
from pathlib import Path
import platform
from time import perf_counter
from openai import AsyncOpenAI,OpenAI
from evals import metrics
from evals.automatic import collect,load_benchmark
from evals.evaluate import append_jsonl,digest,git_state,read_jsonl,timestamp,write_json
from knowledgebase.config import Settings
from knowledgebase.rag.generation import ANSWER_INSTRUCTIONS
DIR=Path(__file__).parent


def inputs():
    frozen=json.loads((DIR/'freeze.json').read_text())
    for name in ('cases','corpus','original-cases'):
        assert digest((DIR/f'{name}.json').read_bytes())==frozen[f'{name}_sha256']
    assert digest(ANSWER_INSTRUCTIONS.encode())==frozen['prompt_sha256']
    assert digest((DIR/'PLAN.md').read_bytes())==frozen['plan_sha256']
    for name, checksum in frozen['baseline_files'].items():
        assert digest(Path(name).read_bytes())==checksum
    _,manifest,docs=load_benchmark()
    assert manifest==json.loads((DIR/'corpus.json').read_text())
    cases=json.loads((DIR/'cases.json').read_text())
    for case in cases:
        for span in case['evidence']+case['context_evidence']:
            assert docs[span['file']][span['start_offset']:span['end_offset']]==span['quote']
    return frozen,cases,docs


async def main():
    frozen,cases,docs=inputs();assert not (DIR/'run.json').exists()
    settings=Settings(**frozen['config'])
    assert not (settings.data_dir/'evals'/DIR.name).exists()
    meta={'started_at':timestamp(),'git':git_state(),'platform':platform.platform(),'status':'running',
        'config':settings.model_dump(mode='json',exclude={'openai_api_key','openai_base_url'}),
        'scope':'Fresh ingestion plus streamed in-process service; no HTTP/browser latency or live lifecycle recheck.',
        'top_k':5,'concurrency':1,'warmup':'none','effective_max_retries':0,'plan_sha256':digest((DIR/'PLAN.md').read_bytes()),
        'cases_sha256':frozen['cases_sha256'],'corpus_sha256':frozen['corpus_sha256'],'reviewer':'Codex'}
    calls=[];start=perf_counter();write_json(DIR/'run.json',meta)
    opts=dict(api_key=settings.openai_api_key,base_url=settings.openai_base_url,timeout=settings.eval_timeout_seconds,max_retries=0)
    try:
        with OpenAI(**opts) as sdk:
            async with AsyncOpenAI(**opts) as async_sdk:
                await collect(settings,DIR,meta,cases,docs,sdk,async_sdk,calls)
        meta['status']='collected' if all(r['status']=='ok' for r in read_jsonl(DIR/'answers.jsonl')) else 'failed'
    except Exception as error:
        meta.update(status='failed',error_type=type(error).__name__)
    finally:
        saved={c['call_id'] for c in read_jsonl(DIR/'calls.jsonl')}
        for call in calls:
            if call['call_id'] not in saved:append_jsonl(DIR/'calls.jsonl',call)
        meta.update(finished_at=timestamp(),wall_seconds=perf_counter()-start)
        write_json(DIR/'run.json',meta)
        write_json(DIR/'automatic-metrics.json',metrics.summarize(cases,read_jsonl(DIR/'answers.jsonl'),[],meta,calls))
        print(meta['status'],flush=True)


if __name__=='__main__':asyncio.run(main())
