"""One saved-context generation pass; keep every attempt and baseline unchanged."""
import asyncio
from copy import deepcopy
import json
from pathlib import Path
import platform
from time import perf_counter
from types import SimpleNamespace

from openai import AsyncOpenAI
from evals.automatic import RecordedResponses
from evals.evaluate import append_jsonl, digest, git_state, read_jsonl, timestamp, write_json
from knowledgebase.config import Settings
from knowledgebase.providers.llm import StreamingLLMClient
from knowledgebase.rag.citations import validate_citations
from knowledgebase.rag.generation import ANSWER_INSTRUCTIONS
from knowledgebase.schemas import AnswerSource

DIR = Path(__file__).parent
BASE = DIR.parent / '20260925-grounding-model'
IDS = ['accept-beta-header-scope', 'accept-independent-passfail', 'accept-awards-jobs',
       'accept-unspecified-api-error', 'accept-personal-study-approval']


def inputs():
    frozen = json.loads((DIR / 'freeze.json').read_text())
    for name, checksum in frozen['baseline_files'].items():
        assert digest((BASE / name).read_bytes()) == checksum, name
    assert digest((DIR / 'PLAN.md').read_bytes()) == frozen['plan_sha256']
    assert digest(ANSWER_INSTRUCTIONS.encode()) == frozen['prompt_sha256']
    return frozen


def messages_for(call):
    messages = deepcopy(call['messages'])
    assert [m['role'] for m in messages] == ['user', 'developer']
    assert messages[1]['content'] == ANSWER_INSTRUCTIONS
    return messages


async def collect():
    frozen = inputs()
    assert not any((DIR / f).exists() for f in ('answers.jsonl', 'calls.jsonl', 'run.json'))
    originals = {a['case_id']: a for a in read_jsonl(BASE / 'answers.jsonl')}
    previous = {c['case_id']: c for c in read_jsonl(BASE / 'calls.jsonl') if c['stage'] == 'generation'}
    settings = Settings(**frozen['config'])
    meta = {'started_at': timestamp(), 'git': git_state(), 'platform': platform.platform(),
            'config': frozen['config'], 'baseline': str(BASE), 'status': 'running',
            'scope': 'Fixed-context generation only; rankings/evidence inherited, no retrieval or HTTP.',
            'concurrency': 1, 'max_retries': 0, 'warmup': 'none; provider load/cache uncontrolled',
            'plan_sha256': frozen['plan_sha256'], 'prompt_sha256': frozen['prompt_sha256']}
    write_json(DIR / 'run.json', meta)
    calls = []
    start = perf_counter()
    async with AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url,
                           timeout=settings.eval_timeout_seconds, max_retries=0) as sdk:
        adapter = RecordedResponses(sdk, calls)
        llm = StreamingLLMClient(SimpleNamespace(responses=adapter), settings.answer_model, reasoning_effort=settings.answer_reasoning_effort)
        for identity in IDS:
            original = originals[identity]
            row = {k: deepcopy(original[k]) for k in ('case_id', 'question', 'sources', 'coverage', 'ranking', 'retrieval')}
            row.update(answer='', status='error', citation_check=None, retrieval_observation_origin=str(BASE))
            adapter.case_id = identity
            try:
                async for delta in llm.stream(messages_for(previous[identity])):
                    row['answer'] += delta
                row['status'] = 'ok'
                row['citation_check'] = validate_citations(row['answer'], [AnswerSource(**s) for s in row['sources']]).model_dump()
            except Exception as error:
                row['error_type'] = type(error).__name__
            call = calls[-1]
            row.update(generation_seconds=call.get('seconds'),
                       generation_first_delta_seconds=next((d['seconds'] for d in call.get('deltas', []) if d['delta']), None))
            append_jsonl(DIR / 'calls.jsonl', call)
            append_jsonl(DIR / 'answers.jsonl', row)
            print(identity, row['status'], flush=True)
    meta.update(status='collected', finished_at=timestamp(), generation_wall_seconds=perf_counter()-start)
    write_json(DIR / 'run.json', meta)


if __name__ == '__main__':
    asyncio.run(collect())
