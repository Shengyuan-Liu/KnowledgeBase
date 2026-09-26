"""One controlled correction pass, without reingesting the corpus."""
import asyncio
import importlib
import json
from pathlib import Path
import platform
from shutil import copytree
from time import perf_counter

from openai import OpenAI,AsyncOpenAI
from evals import metrics
from evals.automatic import load_benchmark,chunk_snapshot,chunk_units_hash
from evals.evaluate import digest,git_state,read_jsonl,write_json,timestamp,append_jsonl
from knowledgebase.config import Settings
from knowledgebase.rag.generation import ANSWER_INSTRUCTIONS
from knowledgebase.storage.runtime import open_storage
collector=importlib.import_module('evals.library-runs.20260925-document-representation.collect_existing')
DIR=Path(__file__).parent
BASE=DIR.parent/'20260925-document-scope'


def inputs():
    frozen=json.loads((DIR/'freeze.json').read_text())
    for name in ('cases','corpus','original-cases'):
        assert digest((DIR/(name+'.json')).read_bytes())==frozen[name+'_sha256']
    for name,checksum in frozen['baseline_files'].items():assert digest(Path(name).read_bytes())==checksum
    assert digest((DIR/'PLAN.md').read_bytes())==frozen['plan_sha256']
    assert digest(ANSWER_INSTRUCTIONS.encode())==frozen['prompt_sha256']
    _,manifest,documents=load_benchmark()
    assert manifest==json.loads((DIR/'corpus.json').read_text())
    cases=json.loads((DIR/'cases.json').read_text())
    assert cases==[c for c in json.loads((BASE/'cases.json').read_text()) if c['id']=='accept-unspecified-api-error']
    for c in cases:
        for e in c['evidence']+c['context_evidence']:
            assert documents[e['file']][e['start_offset']:e['end_offset']]==e['quote']
    return frozen,cases,documents


async def main():
    frozen,cases,_=inputs();assert not (DIR/'run.json').exists()
    settings=Settings(**frozen['config']);previous=json.loads((BASE/'run.json').read_text())
    source=Path(previous['config']['data_dir'])/'evals'/BASE.name
    target=settings.data_dir/'evals'/DIR.name
    assert not target.exists()
    source_hashes={str(p.relative_to(source)):digest(p.read_bytes()) for p in source.rglob('*') if p.is_file()}
    copytree(source,target)
    assert source_hashes=={str(p.relative_to(target)):digest(p.read_bytes()) for p in target.rglob('*') if p.is_file()}
    meta=dict(started_at=timestamp(),git=git_state(),platform=platform.platform(),status='running',config=frozen['config'],
              top_k=5,concurrency=1,effective_max_retries=0,warmup='none; copied index, OS/provider caching uncontrolled',
              scope='In-process service on verified index copy; no fresh ingestion, HTTP, local inference or paid judge.',
              index_reused_from=str(source),index_sha256=source_hashes,baseline_run=str(BASE),plan_sha256=frozen['plan_sha256'])
    write_json(DIR/'run.json',meta);calls=[];start=perf_counter()
    opts=dict(api_key=settings.openai_api_key,base_url=settings.openai_base_url,timeout=settings.eval_timeout_seconds,max_retries=0)
    try:
        with open_storage(target) as (sessions,store):
            chunks=chunk_snapshot(sessions)
            assert chunks==json.loads((BASE/'chunks.json').read_text())
            meta['chunk_units_sha256']=chunk_units_hash(chunks);write_json(DIR/'chunks.json',chunks)
            with OpenAI(**opts) as sdk:
                async with AsyncOpenAI(**opts) as async_sdk:
                    await collector.collect_existing(settings,DIR,meta,cases,sessions,store,chunks,sdk,async_sdk,calls)
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
