"""Resume only the two failed v11 assessments, retaining their original inventories."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from time import perf_counter

from openai import OpenAI
from evals import judge
from evals.evaluate import append_jsonl, digest, git_state, read_jsonl, timestamp, write_json
from knowledgebase.config import Settings

DIRECTORY = Path(__file__).parent
ORIGIN = DIRECTORY.parent / '20260925-generation-citations'
BASELINE = DIRECTORY.parent / '20260925T002400Z-semantic-acceptance/parent_child'


def resume(sdk, prior, case, answer):
    row = deepcopy(prior)
    row['prior_review_origin'] = str(ORIGIN / 'reviews.jsonl')
    row['calls'] = []
    row.pop('error_type', None)
    failed = prior['calls'][-1]
    assert prior['status'] == 'error' and failed['status'] == 'error'
    assert prior['protocol_sha256'] == judge.protocol_hash()
    assert prior['answer_sha256'] == digest(json.dumps(answer, sort_keys=True).encode())
    started = perf_counter()
    try:
        assessment = judge.request(sdk, failed['model'], failed['messages'][0]['content'],
            json.loads(failed['messages'][1]['content']), failed['schema'], row['calls'], failed['reasoning_effort'])
        assessment.update(assessment.pop('abstention'))
        assessment['claims'] = [{'claim_id': key, **value,
            'citations': [{'source_id': int(identity), **citation} for identity, citation in value['citations'].items()]}
            for key, value in assessment['claims'].items()]
        row['assessment_attempt'] = assessment
        row['assessment'] = judge.validate_assessment(assessment, case, answer, row['claims'])
        row['status'] = 'ok'
    except Exception as error:
        row.update(status='error', error_type=type(error).__name__)
        if type(error) is ValueError:
            row['validation_error'] = str(error)
    row['seconds'] = perf_counter() - started
    return row


def main():
    assert not (DIRECTORY / 'run.json').exists(), 'Use a new directory for every attempt.'
    frozen = json.loads((ORIGIN / 'freeze.json').read_text())
    settings = Settings(**frozen['config'])
    cases = {c['id']: c for c in json.loads((BASELINE / 'cases.json').read_text())}
    answers = {a['case_id']: a for a in read_jsonl(ORIGIN / 'answers.jsonl')}
    reviews = read_jsonl(ORIGIN / 'reviews.jsonl')
    failed = [r for r in reviews if r['status'] != 'ok']
    assert {r['case_id'] for r in failed} == {'msds-credits', 'msds-industry'}
    metadata = {'started_at': timestamp(), 'git': git_state(), 'scope': 'Two assessment-only retries; no answer regeneration or retrieval.',
        'origin': str(ORIGIN), 'concurrency': 2, 'max_retries': 0, 'timeout_seconds': settings.judge_timeout_seconds,
        'model': settings.judge_model, 'reasoning_effort': settings.judge_reasoning_effort,
        'protocol_sha256': judge.protocol_hash(), 'status': 'running',
        'origin_sha256': {name: digest((ORIGIN / name).read_bytes()) for name in ('answers.jsonl', 'reviews.jsonl', 'calls.jsonl', 'freeze.json')}}
    write_json(DIRECTORY / 'run.json', metadata)
    start = perf_counter()
    with OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url,
                timeout=settings.judge_timeout_seconds, max_retries=0) as sdk, ThreadPoolExecutor(max_workers=2) as pool:
        completed = list(pool.map(lambda r: resume(sdk, r, cases[r['case_id']], answers[r['case_id']]), failed))
    for row in completed:
        append_jsonl(DIRECTORY / 'supplemental-reviews.jsonl', row)
        for call in row['calls']:
            append_jsonl(DIRECTORY / 'supplemental-calls.jsonl', {**call, 'stage': 'judge', 'case_id': row['case_id']})
        print(row['case_id'], row['status'], flush=True)
    replacement = {r['case_id']: r for r in completed}
    # Derived views reuse exact historical bytes; only the new assessment calls incur new usage.
    for name in ('answers.jsonl', 'freeze.json'):
        (DIRECTORY / name).write_bytes((ORIGIN / name).read_bytes())
    for row in reviews:
        append_jsonl(DIRECTORY / 'reviews.jsonl', replacement.get(row['case_id'], row))
    (DIRECTORY / 'calls.jsonl').write_bytes((ORIGIN / 'calls.jsonl').read_bytes() + (DIRECTORY / 'supplemental-calls.jsonl').read_bytes())
    metadata.update(status='completed' if all(r['status'] == 'ok' for r in completed) else 'pending_reviews',
                    finished_at=timestamp(), wall_seconds=perf_counter()-start)
    write_json(DIRECTORY / 'run.json', metadata)
    spec = importlib.util.spec_from_file_location('replay', ORIGIN / 'run_replay.py')
    replay = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(replay)
    replay.DIRECTORY = DIRECTORY
    replay.summaries(json.loads((ORIGIN / 'run.json').read_text()))


if __name__ == '__main__':
    main()
