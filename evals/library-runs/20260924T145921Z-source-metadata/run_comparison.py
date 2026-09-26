"""Replay fixed BGE candidates; compare old/new identity formatting and budget packing."""

import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from time import perf_counter
from types import SimpleNamespace

from openai import AsyncOpenAI
import tiktoken

from evals.evaluate import retrieval_metrics
from knowledgebase.config import Settings
from knowledgebase.providers.llm import StreamingLLMClient
from knowledgebase.rag import context, generation, packing
from knowledgebase.schemas import ChildChunk, StructuredChunk, RetrievedChunk, RetrievalDiagnostics


ROOT = Path(__file__).parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def inputs(row, files):
    children = {c['chunk_id']: ChildChunk.model_validate(c) for f in files for c in f['chunks']}
    parents = {p['parent_id']: p for f in files for p in f['parents']}
    names = {f['file']['file_id']: f['file']['file_name'] for f in files}
    selected, expanded = [], {}
    for c in row['answer']['retrieval']['candidates']:
        child = children[c['chunk_id']]
        hit = RetrievedChunk(chunk=child, file_name=names[child.file_id],
                             distance=c['distance'], fusion=c['fusion'], rerank=c['rerank'],
                             parent_id=child.parent_id, matched_child_ids=[child.chunk_id])
        selected.append(hit)
        if child.parent_id not in expanded:
            parent = parents[child.parent_id]
            expanded[child.parent_id] = hit.model_copy(update={
                'chunk': StructuredChunk(chunk_id=child.parent_id, **{k: v for k, v in parent.items() if k != 'parent_id'}),
                'matched_child_ids': [],
            })
        expanded[child.parent_id].matched_child_ids.append(child.chunk_id)
    return selected, list(expanded.values())


def sources(result):
    return [{**item.chunk.model_dump(), 'source_id': i, 'file_name': item.file_name,
             'parent_id': item.parent_id, 'matched_child_ids': item.matched_child_ids,
             'distance': item.distance, 'fusion': item.fusion.model_dump(), 'rerank': item.rerank.model_dump()}
            for i, item in enumerate(result.chunks, 1)]


async def run():
    settings = Settings()
    frozen = [json.loads(line) for line in (ROOT / 'frozen-evidence.jsonl').read_text().splitlines()]
    files = json.loads((ROOT / 'chunks.json').read_text())
    cases = {c['id']: c for c in json.loads((ROOT / 'cases.json').read_text())}
    old_context = module('old_context', ROOT / 'baseline_context.py').build_context
    old_prompt = module('old_generation', ROOT / 'baseline_generation.py').ANSWER_INSTRUCTIONS
    recorded = module('recorded', ROOT.parent / '20260924T012523Z-source-attribution-v2/run_comparison.py')
    new_context, new_prompt = context.build_context, generation.ANSWER_INSTRUCTIONS
    metadata = {
        'scope': 'Frozen top-5 child selections; fresh budget packing and production streamed generation.',
        'base_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'code_hashes': {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in
                        ['knowledgebase/rag/context.py', 'knowledgebase/rag/generation.py', 'knowledgebase/rag/packing.py']},
        'input_hashes': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in
                         ['cases.json', 'chunks.json', 'frozen-evidence.jsonl']},
        'answer_model': settings.answer_model, 'concurrency': 1,
        'timeout_seconds': settings.eval_timeout_seconds, 'max_retries': 0,
        'evidence_max_tokens': 4096, 'warmup': 'none; provider cache and host/network load uncontrolled',
        'retrieval_options': settings.retrieval_options.model_dump(),
        'timing_scope': 'Separate packing and generation; generation SDK stream excludes retrieval and app HTTP.',
        'judge': 'No provider judge run: prior observed claim-omission failures remain unresolved.',
    }
    with (ROOT / 'run.json').open('x') as out:
        json.dump(metadata, out, indent=2)
    (ROOT / 'candidate-prompt.txt').write_text(new_prompt)
    sdk_options = {'api_key': settings.openai_api_key, 'timeout': settings.eval_timeout_seconds, 'max_retries': 0}
    if settings.openai_base_url:
        sdk_options['base_url'] = settings.openai_base_url
    encoding = tiktoken.get_encoding('cl100k_base')
    batch_start = perf_counter()
    async with AsyncOpenAI(**sdk_options) as sdk:
        with (ROOT / 'answers.jsonl').open('x') as out:
            for index, original in enumerate(frozen):
                modes = ['baseline', 'candidate'] if index % 2 == 0 else ['candidate', 'baseline']
                case = cases[original['case_id']]
                case = {**case, 'evidence': [{**e, 'file': Path(e['file']).name} for e in case['evidence']]}
                for mode in modes:
                    formatter, prompt = (old_context, old_prompt) if mode == 'baseline' else (new_context, new_prompt)
                    packing.build_context = generation.build_context = formatter
                    packing.CONTEXT_FORMAT = 'numbered-text-v1' if mode == 'baseline' else context.CONTEXT_FORMAT
                    generation.ANSWER_INSTRUCTIONS = prompt
                    selected, expanded = inputs(original, files)
                    diagnostics = RetrievalDiagnostics.model_validate(original['answer']['retrieval'])
                    # Reranking was frozen, so its old duration is not a new stage measurement.
                    diagnostics.rerank_seconds = None
                    result = packing.pack_evidence(selected, expanded, diagnostics)
                    supplied = sources(result)
                    if mode == 'baseline':
                        assert [(s['chunk_id'], s['text']) for s in supplied] == [
                            (s['chunk_id'], s['text']) for s in original['answer']['sources']]
                    tokens = len(encoding.encode_ordinary(formatter(result.chunks)))
                    assert tokens == result.diagnostics.evidence_tokens <= 4096
                    row = {'case_id': case['id'], 'question': case['question'], 'strategy': mode,
                           'sources': supplied, 'retrieval': result.diagnostics.model_dump(),
                           'coverage': retrieval_metrics(case, supplied), 'deltas': [], 'usage': None, 'retries': 0}
                    started = perf_counter()
                    wrapper = SimpleNamespace(responses=recorded.RecordedResponses(sdk, row, started))
                    try:
                        row['answer'] = ''.join([part async for part in generation.stream_answer(
                            case['question'], result.chunks, StreamingLLMClient(wrapper, settings.answer_model))])
                        row['status'] = 'ok'
                    except Exception as error:
                        row.update(status='error', error_type=type(error).__name__,
                                   answer=''.join(d['delta'] for d in row['deltas']))
                    row['total_seconds'] = perf_counter() - started
                    row['first_delta_seconds'] = next((d['seconds'] for d in row['deltas'] if d['delta']), None)
                    out.write(json.dumps(row) + '\n')
                    out.flush()
                    print(mode, case['id'], row['status'], row['coverage']['annotated_char_recall'],
                          tokens, round(row['total_seconds'], 2), flush=True)
    with (ROOT / 'batch.json').open('x') as out:
        json.dump({'wall_seconds': perf_counter() - batch_start, 'attempts': len(frozen) * 2}, out, indent=2)


if __name__ == '__main__':
    asyncio.run(run())
