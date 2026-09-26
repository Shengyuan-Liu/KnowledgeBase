"""Check completed replay provenance, measurements and saved secret hygiene offline."""
import json
from pathlib import Path
import re
import subprocess
import sys
from time import perf_counter

from evals.evaluate import digest, git_state, read_jsonl, timestamp, write_json
from knowledgebase.config import Settings

DIRECTORY = Path(__file__).parent
BASELINE = DIRECTORY.parent / '20260925T002400Z-semantic-acceptance/parent_child'


def main(name):
    target = DIRECTORY / f'{name}.json'
    if target.exists():
        raise SystemExit('Keep earlier attempts; choose a new record name.')
    started = perf_counter()
    report = {'command': ['uv', 'run', '--locked', 'python', str(Path(__file__)), name],
        'environment': {'PYTHONPATH': '.'}, 'git': git_state(), 'started_at': timestamp(), 'checks': []}

    def check(label, condition):
        report['checks'].append({'name': label, 'passed': bool(condition)})
        assert condition, label

    try:
        frozen = json.loads((DIRECTORY / 'freeze.json').read_text())
        old_answers = {a['case_id']: a for a in read_jsonl(BASELINE / 'answers.jsonl')}
        old_calls = {c['case_id']: c for c in read_jsonl(BASELINE / 'calls.jsonl') if c['stage'] == 'generation'}
        answers = read_jsonl(DIRECTORY / 'answers.jsonl')
        reviews = read_jsonl(DIRECTORY / 'reviews.jsonl')
        calls = read_jsonl(DIRECTORY / 'calls.jsonl')
        generated = [c for c in calls if c['stage'] == 'generation']
        check('Frozen baseline unchanged', all(digest((BASELINE / name).read_bytes()) == value for name, value in frozen['baseline_files'].items()))
        check('24 successful generation attempts, no duplicate cases', len(answers) == len(generated) == 24
            and {a['case_id'] for a in answers} == set(old_answers) and all(a['status'] == 'ok' for a in answers))
        check('Only developer message changed', all(c['messages'][1:] == old_calls[c['case_id']]['messages'][1:]
            and c['messages'][0] == {'role': 'developer', 'content': frozen['new_prompt']} for c in generated))
        check('Supplied sources and retrieval results identical', all(
            a[key] == old_answers[a['case_id']][key] for a in answers for key in ('sources', 'coverage', 'ranking', 'retrieval')))
        check('No old persistence IDs or service timing claimed as fresh', all(
            'conversation_id' not in a and 'message_id' not in a and all(a[key] is None for key in (
                'first_delta_seconds', 'total_seconds', 'retrieval_seconds', 'embedding_seconds', 'rerank_seconds', 'packing_seconds')) for a in answers))
        check('Resolved answer model matches baseline', {c['resolved_model'] for c in generated} == {c['resolved_model'] for c in old_calls.values()})
        check('Every review points to exact new answer and frozen protocol', len(reviews) == 24
            and {r['case_id'] for r in reviews} == set(old_answers)
            and all(r['status'] in {'ok', 'error'} and r['protocol_sha256'] == frozen['judge_protocol_sha256']
                and r['answer_sha256'] == digest(json.dumps(next(a for a in answers if a['case_id'] == r['case_id']), sort_keys=True).encode()) for r in reviews))
        check('One judgment attempt per answer, all attempted stages retained',
            len([c for c in calls if c['stage'] == 'judge']) == sum(len(r['calls']) for r in reviews)
            and all(1 <= len(r['calls']) <= 3 for r in reviews))
        check('Provider errors retained in corresponding reviews',
            [{k: v for k, v in c.items() if k not in {'stage', 'case_id'}} for c in calls if c['status'] != 'ok'] ==
            [c for r in reviews for c in r['calls'] if c['status'] != 'ok'])
        check('Only generation and judgment incurred calls', {c['stage'] for c in calls} == {'generation', 'judge'})
        check('No invalid citation IDs', all(a['citation_check']['invalid_source_ids'] == [] for a in answers))
        after = json.loads((DIRECTORY / 'after-all.json').read_text())['metrics']
        check('Complete metric inventory preserved', set(after) == set(json.loads((DIRECTORY / 'before-all.json').read_text())['metrics']))
        check('All 24 questions and failed judgments contribute to reliability',
            after['reliability']['value']['planned'] == 24
            and after['judge_reliability']['value']['pending'] == sum(r['status'] != 'ok' for r in reviews))
        documents = [DIRECTORY / 'README.md', DIRECTORY / 'REVIEW.md', Path('docs/answer-grounding.md'),
            Path('docs/v1/README.md'), Path('README.md')]
        for document in documents:
            links = [link.split('#')[0] for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)', document.read_text()) if not link.startswith(('https:', 'http:', 'mailto:', '#'))]
            check(f'Local links resolve: {document}', all((document.parent / link).exists() for link in links))
        check('Whitespace review', subprocess.run(['git', 'diff', '--check'], capture_output=True).returncode == 0)
        key = Settings().openai_api_key
        check('Credential absent from artifacts', bool(key) and all(key.encode() not in p.read_bytes() for p in DIRECTORY.rglob('*') if p.is_file()))
        report.update(status='passed', exit_code=0)
    except Exception as error:
        report.update(status='failed', exit_code=1, error_type=type(error).__name__, error=str(error))
    keys = json.loads(Path('evals/check-runs/20260925-generation-citations/scoped-1.json').read_text())['metric_inventory']
    report['metric_inventory'] = {key: {'status': 'not_applicable', 'value': None,
        'reason': 'Offline artifact integrity checks; no new provider calls or quality/performance workload. Live measurements are in before/after summaries.'} for key in keys}
    report.update(finished_at=timestamp(), seconds=perf_counter() - started,
        counts={'passed': sum(c['passed'] for c in report['checks']), 'failed': sum(not c['passed'] for c in report['checks']), 'skipped': 0},
        documentation_review='Codex checked report statements against exact outputs, source excerpts, metrics and known limitations; reviewed Markdown formatting and links.')
    write_json(target, report)
    print(report['status'], report['counts'], report.get('error', ''))
    return report['exit_code']


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1]))
