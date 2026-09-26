"""Replay frozen user/evidence messages once with the completed generation prompt."""
import asyncio
from copy import deepcopy
import json
from pathlib import Path
import platform
import sys
from time import perf_counter
from types import SimpleNamespace

from openai import AsyncOpenAI, OpenAI

from evals import judge, metrics
from evals.automatic import RecordedResponses, grade
from evals.evaluate import append_jsonl, digest, git_state, read_jsonl, timestamp, write_json
from knowledgebase.config import Settings
from knowledgebase.providers.llm import StreamingLLMClient
from knowledgebase.rag.citations import validate_citations
from knowledgebase.rag.generation import ANSWER_INSTRUCTIONS
from knowledgebase.schemas import AnswerSource

DIRECTORY = Path(__file__).parent
BASELINE = DIRECTORY.parent / '20260925T002400Z-semantic-acceptance/parent_child'
STAGES_NOT_RUN = ('first_delta_seconds', 'total_seconds', 'retrieval_seconds',
                  'embedding_seconds', 'rerank_seconds', 'packing_seconds')


def messages_for(call):
    messages = deepcopy(call['messages'])
    assert len(messages) == 2 and messages[0]['role'] == 'developer' and messages[1]['role'] == 'user'
    messages[0]['content'] = ANSWER_INSTRUCTIONS
    return messages


def replay_row(original):
    row = deepcopy(original)
    for key in STAGES_NOT_RUN:
        row[key] = None
    for key in ('conversation_id', 'message_id', 'events'):
        row.pop(key, None)
    row['retrieval_observation_origin'] = str(BASELINE)
    return row


def inputs():
    frozen = json.loads((DIRECTORY / 'freeze.json').read_text())
    for name, checksum in frozen['baseline_files'].items():
        assert digest((BASELINE / name).read_bytes()) == checksum, name
    assert judge.protocol_hash() == frozen['judge_protocol_sha256']
    assert digest(ANSWER_INSTRUCTIONS.encode()) == frozen['new_prompt_sha256']
    return frozen, json.loads((BASELINE / 'cases.json').read_text()), read_jsonl(BASELINE / 'answers.jsonl')


def summaries(metadata):
    _, cases, originals = inputs()
    baseline_meta = json.loads((BASELINE / 'run.json').read_text())
    old_reviews = read_jsonl(BASELINE / 'reviews.jsonl')
    answers, reviews, calls = (read_jsonl(DIRECTORY / f'{kind}.jsonl') for kind in ('answers', 'reviews', 'calls'))
    old_calls = [c for c in read_jsonl(BASELINE / 'calls.jsonl') if c['stage'] in ('generation', 'judge')]
    comparisons = {}
    for split in ('all', 'development-regression', 'new-frozen-acceptance'):
        subset = [c for c in cases if split == 'all' or c['split'] == split]
        ids = {c['id'] for c in subset}
        results = []
        for label, rows, assessments, observed in (
            ('before', [replay_row(a) for a in originals], old_reviews, old_calls),
            ('after', answers, reviews, calls),
        ):
            summary = metrics.summarize(subset, [a for a in rows if a['case_id'] in ids],
                [r for r in assessments if r['case_id'] in ids], {'top_k': baseline_meta['top_k']},
                [c for c in observed if c.get('case_id') in ids])
            summary['limitations'] = [
                'Fixed historical contexts; all questions are now development/regression cases, including the six previously new questions.',
                'Only developer instructions change; baseline answers and valid v11 reviews are reused. Single-pass historical comparison, provider variation uncontrolled.',
                'LLM assessments are not ground truth. Codex inspection is not independent human review.',
                'Generation-only timing; no fresh retrieval, HTTP transport or persistence. Historical stage traces remain evidence provenance only.',
            ]
            for key in (*STAGES_NOT_RUN, 'search_fusion_seconds', 'ingestion', 'update_delete', 'model_loading'):
                summary['metrics'][key] = metrics.missing('Not exercised in this saved-context generation comparison.', False)
            for key in ('ingestion', 'query_embedding'):
                summary['metrics']['token_usage'][key] = metrics.missing('No ingestion or query embedding calls in replay.', False)
            summary['metrics']['reliability']['method'] = 'Planned saved-context generation requests; no retries, partial answers fail.'
            for key in ('recall_at_k', 'precision_at_k', 'hit_rate_at_k', 'mrr_at_k', 'ndcg_at_k', 'annotated_char_recall', 'full_evidence_recall'):
                summary['metrics'][key]['origin'] = 'Frozen retrieval observations; unchanged, not a new retrieval measurement.'
            if label == 'after' and split == 'all' and metadata.get('generation_wall_seconds'):
                duration = metadata['generation_wall_seconds']
                summary['metrics']['concurrency_throughput'] = metrics.measured(
                    {'concurrency': 1, 'wall_seconds': duration, 'successful_requests_per_second': sum(a['status'] == 'ok' for a in answers) / duration},
                    'requests/second', len(answers), 'Sequential generation replay including logging; not full RAG load capacity.')
            write_json(DIRECTORY / f'{label}-{split}.json', summary)
            results.append(summary)
        valid = all(s['metrics']['judge_reliability']['value']['pending'] == 0 for s in results)
        resolved = [{c['resolved_model'] for c in group if c.get('stage') == 'judge' and c.get('resolved_model')} for group in (old_calls, calls)]
        same_judge = bool(resolved[0]) and resolved[0] == resolved[1]
        comparisons[split] = metrics.compare(*results, quality_compatible=valid and same_judge,
            timing_compatible=False, ranking_compatible=True, same_judge_protocol=same_judge)
    write_json(DIRECTORY / 'comparison.json', comparisons)


async def collect():
    frozen, cases, originals = inputs()
    if (DIRECTORY / 'answers.jsonl').exists() or (DIRECTORY / 'run.json').exists():
        raise ValueError('Use a new run directory for another paid attempt.')
    settings = Settings(**frozen['config'])
    original_calls = {c['case_id']: c for c in read_jsonl(BASELINE / 'calls.jsonl') if c['stage'] == 'generation'}
    metadata = {'started_at': timestamp(), 'git': git_state(), 'platform': platform.platform(),
        'config': frozen['config'], 'baseline': str(BASELINE), 'status': 'running',
        'scope': 'Generation replay; original user/evidence messages unchanged; no ingestion or retrieval.',
        'concurrency': 1, 'max_retries': 0, 'warmup': 'none; provider/host load uncontrolled',
        'judge_protocol': judge.PROTOCOL, 'judge_protocol_sha256': judge.protocol_hash()}
    write_json(DIRECTORY / 'run.json', metadata)
    calls = []
    start = perf_counter()
    async with AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url,
                           timeout=settings.eval_timeout_seconds, max_retries=0) as sdk:
        adapter = RecordedResponses(sdk, calls)
        llm = StreamingLLMClient(SimpleNamespace(responses=adapter), settings.answer_model)
        for original in originals:
            row = replay_row(original)
            row.update(answer='', status='error', citation_check=None, generation_seconds=None, generation_first_delta_seconds=None)
            adapter.case_id = row['case_id']
            try:
                async for delta in llm.stream(messages_for(original_calls[row['case_id']])):
                    row['answer'] += delta
                row['status'] = 'ok'
                row['citation_check'] = validate_citations(row['answer'], [AnswerSource(**s) for s in row['sources']]).model_dump()
            except Exception as error:
                row['error_type'] = type(error).__name__
            call = calls[-1]
            row.update(generation_seconds=call.get('seconds'),
                generation_first_delta_seconds=next((d['seconds'] for d in call.get('deltas', []) if d['delta']), None))
            append_jsonl(DIRECTORY / 'calls.jsonl', call)
            append_jsonl(DIRECTORY / 'answers.jsonl', row)
            print(row['case_id'], row['status'], flush=True)
    metadata.update(status='collected', collection_finished_at=timestamp(), generation_wall_seconds=perf_counter() - start)
    write_json(DIRECTORY / 'run.json', metadata)
    summaries(metadata)


def assess():
    frozen, cases, _ = inputs()
    if (DIRECTORY / 'reviews.jsonl').exists():
        raise ValueError('Preserve this judgment attempt; do not regrade here.')
    settings = Settings(**frozen['config'])
    metadata = json.loads((DIRECTORY / 'run.json').read_text())
    with OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url,
                timeout=settings.eval_timeout_seconds, max_retries=0) as sdk:
        reviews = grade(sdk, settings, cases, read_jsonl(DIRECTORY / 'answers.jsonl'), DIRECTORY)
    metadata.update(status='completed' if len(reviews) == len(cases) and all(r['status'] == 'ok' for r in reviews) else 'pending_reviews', finished_at=timestamp())
    write_json(DIRECTORY / 'run.json', metadata)
    summaries(metadata)


if __name__ == '__main__':
    if sys.argv[1] == 'collect':
        asyncio.run(collect())
    elif sys.argv[1] == 'grade':
        assess()
    else:
        raise SystemExit('Choose collect or grade.')
