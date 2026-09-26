"""Apply the existing evidence-validated judge protocol to both prompt arms."""

import asyncio
import json
from pathlib import Path
from time import perf_counter

from openai import AsyncOpenAI

from evals.evaluate import judge_messages, judge_protocol_hash, validate_assessment
from knowledgebase.config import Settings


ROOT = Path(__file__).parent


async def run():
    settings = Settings()
    cases = {c['id']: c for c in json.loads((ROOT / 'cases.json').read_text())}
    rows = [json.loads(line) for line in (ROOT / 'answers.jsonl').read_text().splitlines()]
    sdk_options = {'api_key': settings.openai_api_key, 'timeout': settings.eval_timeout_seconds, 'max_retries': 0}
    if settings.openai_base_url:
        sdk_options['base_url'] = settings.openai_base_url
    async with AsyncOpenAI(**sdk_options) as sdk:
        with (ROOT / 'judge.jsonl').open('x') as output:
            semaphore = asyncio.Semaphore(3)

            async def assess(row):
                async with semaphore:
                    case = cases[row['case_id']]
                    messages = judge_messages(case, row)
                    record = {'case_id': row['case_id'], 'strategy': row['strategy'],
                              'reviewer': settings.judge_model, 'method': 'LLM judge, not human',
                              'protocol_sha256': judge_protocol_hash(), 'messages': messages,
                              'concurrency': 3, 'retries': 0, 'usage': None}
                    start = perf_counter()
                    try:
                        response = await sdk.responses.create(model=settings.judge_model, input=messages,
                            text={'format': {'type': 'json_schema', 'name': 'rag_assessment', 'strict': True,
                                             'schema': json.loads(messages[1]['content'])['schema']}})
                        record['raw'] = response.output_text
                        record['usage'] = response.usage.model_dump() if response.usage else None
                        record['resolved_model'] = response.model
                        rating, assessment = validate_assessment(case, row, json.loads(response.output_text))
                        record.update(status='ok', rating=rating, assessment=assessment)
                    except Exception as error:
                        record.update(status='error', error_type=type(error).__name__)
                    record['seconds'] = perf_counter() - start
                    output.write(json.dumps(record) + '\n')
                    output.flush()
                    print(row['strategy'], row['case_id'], record['status'], flush=True)

            await asyncio.gather(*(assess(row) for row in rows if row['status'] == 'ok'))


if __name__ == '__main__':
    asyncio.run(run())
