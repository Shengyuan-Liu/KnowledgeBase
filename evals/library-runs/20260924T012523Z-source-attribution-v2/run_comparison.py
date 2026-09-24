"""Compare production generation prompts with byte-identical frozen evidence."""

import asyncio
import hashlib
import json
from pathlib import Path
import subprocess
from time import perf_counter
from types import SimpleNamespace

from openai import AsyncOpenAI

from knowledgebase.config import Settings
from knowledgebase.providers.llm import StreamingLLMClient
from knowledgebase.rag import generation
from knowledgebase.schemas import Chunk, RetrievedChunk


ROOT = Path(__file__).parent


class RecordedStream:
    def __init__(self, stream, row, start):
        self.stream, self.row, self.start = stream, row, start

    def __aiter__(self):
        return self

    async def __anext__(self):
        event = await anext(self.stream)
        elapsed = perf_counter() - self.start
        if event.type == 'response.output_text.delta':
            self.row['deltas'].append({'seconds': elapsed, 'delta': event.delta})
        elif event.type == 'response.completed':
            self.row['provider_complete_seconds'] = elapsed
            self.row['resolved_model'] = event.response.model
            self.row['usage'] = event.response.usage.model_dump() if event.response.usage else None
        return event

    async def close(self):
        await self.stream.close()


class RecordedResponses:
    def __init__(self, sdk, row, start):
        self.sdk, self.row, self.start = sdk, row, start

    async def create(self, **kwargs):
        self.row['messages'] = kwargs['input']
        stream = await self.sdk.responses.create(**kwargs)
        return RecordedStream(stream, self.row, self.start)


async def run():
    settings = Settings()
    frozen = [json.loads(line) for line in (ROOT / 'frozen-evidence.jsonl').read_text().splitlines()]
    prompts = {mode: (ROOT / f'{mode}-prompt.txt').read_text() for mode in ['baseline', 'candidate']}
    assert prompts['candidate'] == generation.ANSWER_INSTRUCTIONS
    metadata = {
        'scope': 'Live production generation replay; retrieval and packing frozen, not rerun.',
        'base_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'generation_sha256': hashlib.sha256(Path(generation.__file__).read_bytes()).hexdigest(),
        'input_hashes': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                         for name in ['cases.json', 'chunks.json', 'frozen-evidence.jsonl',
                                      'baseline-prompt.txt', 'candidate-prompt.txt']},
        'answer_model': settings.answer_model, 'judge_model': settings.judge_model,
        'concurrency': 1, 'timeout_seconds': settings.eval_timeout_seconds,
        'max_retries': 0, 'warmup': 'none; provider cache behavior uncontrolled',
        'retrieval_options': settings.retrieval_options.model_dump(),
        'evidence_max_tokens': settings.evidence_max_tokens,
        'timing_scope': 'SDK generation request start to first nonempty delta and stream close; excludes retrieval and app HTTP.',
    }
    with (ROOT / 'run.json').open('x') as output:
        json.dump(metadata, output, indent=2)
    sdk_options = {'api_key': settings.openai_api_key, 'timeout': settings.eval_timeout_seconds, 'max_retries': 0}
    if settings.openai_base_url:
        sdk_options['base_url'] = settings.openai_base_url
    batch_start = perf_counter()
    async with AsyncOpenAI(**sdk_options) as sdk:
        with (ROOT / 'answers.jsonl').open('x') as output:
            for index, original in enumerate(frozen):
                modes = ['baseline', 'candidate'] if index % 2 == 0 else ['candidate', 'baseline']
                sources = original['answer']['sources']
                chunks = [RetrievedChunk(chunk=Chunk(
                    chunk_id=s['chunk_id'], file_id=s['file_id'], index=i, text=s['text'],
                    start_offset=s['start_offset'], end_offset=s['end_offset']),
                    file_name=s['file_name'], distance=s['distance']) for i, s in enumerate(sources)]
                for mode in modes:
                    generation.ANSWER_INSTRUCTIONS = prompts[mode]
                    row = {'case_id': original['case_id'], 'question': original['question'],
                           'strategy': mode, 'sources': sources, 'coverage': original['coverage'],
                           'deltas': [], 'usage': None, 'retries': 0}
                    started = perf_counter()
                    wrapper = SimpleNamespace(responses=RecordedResponses(sdk, row, started))
                    try:
                        parts = [part async for part in generation.stream_answer(
                            row['question'], chunks, StreamingLLMClient(wrapper, settings.answer_model))]
                        row['answer'] = ''.join(parts)
                        row['status'] = 'ok'
                    except Exception as error:
                        row.update(status='error', error_type=type(error).__name__,
                                   answer=''.join(d['delta'] for d in row['deltas']))
                    row['total_seconds'] = perf_counter() - started
                    row['first_delta_seconds'] = next((d['seconds'] for d in row['deltas'] if d['delta']), None)
                    output.write(json.dumps(row) + '\n')
                    output.flush()
                    print(mode, row['case_id'], row['status'], round(row['total_seconds'], 2), flush=True)
    with (ROOT / 'batch.json').open('x') as output:
        json.dump({'wall_seconds': perf_counter() - batch_start, 'attempts': len(frozen) * 2}, output, indent=2)


if __name__ == '__main__':
    asyncio.run(run())
