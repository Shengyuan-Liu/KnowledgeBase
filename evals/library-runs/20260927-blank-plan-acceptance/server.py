"""Real isolated API server with evaluation-only observation and snapshot endpoints."""
from contextlib import asynccontextmanager
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
from time import perf_counter

from openai import OpenAI, AsyncOpenAI
import uvicorn

from observability import SyncObserver, AsyncObserver, REQUEST, ROOT, log
import knowledgebase.api.app as app_module
from knowledgebase.api.dependencies import Resources
from knowledgebase.storage.operations import get_files, get_pdf_extraction, get_chunks, get_parents
from knowledgebase.services.pdf import LocalPdfParser
import knowledgebase.services.chat as chat
import knowledgebase.services.hops as hops

DATA = Path('data/evals/20260927-blank-plan-acceptance').resolve()
app_module.OpenAI = lambda **kwargs: SyncObserver(OpenAI(**kwargs))
app_module.AsyncOpenAI = lambda **kwargs: AsyncObserver(AsyncOpenAI(**kwargs))


def observe(name, fn):
    def call(*args, **kwargs):
        started = perf_counter()
        result = fn(*args, **kwargs)
        if name == 'parse':
            log('stage', stage=name, seconds=perf_counter()-started,
                pages=len(result.pages), parser=result.parser.model_dump(mode='json'))
        else:
            log('stage', stage=name, seconds=perf_counter()-started, result=result.model_dump(mode='json'))
        return result
    return call

LocalPdfParser.parse = observe('parse', LocalPdfParser.parse)
chat.retrieve_evidence = observe('single_retrieval', chat.retrieve_evidence)
hops.retrieve_plan = observe('planned_retrieval', hops.retrieve_plan)
chat.retrieve_plan = observe('planned_retrieval', chat.retrieve_plan)
api = app_module.create_app(data_dir=DATA, frontend_dir=ROOT / "no-frontend")
original_lifespan = api.router.lifespan_context


@asynccontextmanager
async def lifespan(app):
    started = perf_counter()
    async with original_lifespan(app):
        resources = app.state.resources
        safe = resources.settings.model_dump(mode='json', exclude={'openai_api_key', 'openai_base_url'})
        safe['data_dir'] = str(DATA)
        path = ROOT / 'resolved-runtime.json'
        assert not path.exists(), 'Do not restart a live attempt into the same output files.'
        path.write_text(json.dumps(dict(settings=safe, startup_seconds=perf_counter()-started,
            code_commit=subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
            source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('knowledgebase').rglob('*.py')},
            harness_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.py')},
            device=platform.platform(), python=platform.python_version(),
            packages={name:importlib.metadata.version(name) for name in ['docling','pdfplumber','pdfminer.six','openai','chromadb','torch','transformers','tiktoken']},
            reranker=dict(model=resources.reranker.model, revision=resources.reranker.model_revision,
                          device=resources.reranker.device) if resources.reranker else None), indent=2)+'\n')
        yield

api.router.lifespan_context = lifespan


@api.get('/__eval__/snapshot')
def snapshot(resources: Resources):
    with resources.sessions() as session:
        return {'files': [dict(file=f.model_dump(mode='json'),
            extraction=get_pdf_extraction(session, f.file_id).model_dump(mode='json'),
            chunks=[c.model_dump(mode='json') for c in get_chunks(session, f.file_id)],
            parents=[c.model_dump(mode='json') for c in get_parents(session, f.file_id)])
            for f in get_files(session) if f.status == 'ready'],
            'index_bytes': sum(p.stat().st_size for p in DATA.rglob('*') if p.is_file())}


class RequestObserver:
    async def __call__(self, scope, receive, send):
        headers = dict(scope.get('headers', []))
        token = REQUEST.set(headers.get(b'x-eval-id', b'unlabeled').decode())
        try:
            await api(scope, receive, send)
        finally:
            REQUEST.reset(token)


if __name__ == '__main__':
    uvicorn.run(RequestObserver(), host='127.0.0.1', port=8786, log_level='warning')
