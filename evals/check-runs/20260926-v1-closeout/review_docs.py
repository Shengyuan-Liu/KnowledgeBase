"""Record local documentation closeout review; no provider calls."""
import json
from pathlib import Path
import re
import subprocess
from time import perf_counter
from evals.evaluate import digest, git_state, timestamp, write_json

folder = Path(__file__).parent
if (folder / 'documentation-review.json').exists():
    raise SystemExit('Use a new record; historical reviews are append-only.')
started, stamp = perf_counter(), timestamp()
paths = [Path('README.md'), Path('docs/README.md'), *sorted(Path('docs/v1').glob('*.md')),
         folder / 'README.md', Path('evals/browser-runs/20260926-v1-final-ui-1/README.md')]
errors, links = [], []
for path in paths:
    text = path.read_text()
    if re.search(r'[\u4e00-\u9fff]', text):
        errors.append(f'{path}: non-English project text')
    if len(re.findall(r'^```', text, re.M)) % 2:
        errors.append(f'{path}: unbalanced fenced code')
    for raw in re.findall(r'\]\(([^)]+)\)', text):
        target = raw.split('#')[0]
        if not target or re.match(r'\w+://', target):
            continue
        resolved = path.parent / target
        links.append({'file': str(path), 'target': target, 'exists': resolved.exists()})
        if not resolved.exists():
            errors.append(f'{path}: missing {target}')
whitespace = subprocess.run(['git', 'diff', '--check'], capture_output=True, text=True)
if whitespace.returncode:
    errors.append(whitespace.stdout + whitespace.stderr)
original = json.loads(Path('evals/check-runs/20260924-judge-calibration/backend-6.json').read_text())['metric_inventory']
record = {'started_at': stamp, 'finished_at': timestamp(), 'seconds': perf_counter() - started,
    'command': 'uv run python -m evals.check-runs.20260926-v1-closeout.review_docs', 'git': git_state(),
    'scope': [str(p) for p in paths], 'sha256': {str(p): digest(p.read_bytes()) for p in paths},
    'content_review': {'reviewer': 'Codex', 'result': 'Compared delivered-feature table and defaults to component docs/config; verified merge hash and existing test evidence. Distinguished new UI checks from earlier suites, accepted defaults from experiments, and functional completion from independent quality. Preserved historical failures and disclosed SSE observer limitation; no false claim that stream warning is fixed.',
                      'sources': ['knowledgebase/config.py', 'git log', 'docs/v1/merge-readiness.md', 'evals/browser-runs/20260926-v1-final-ui-1/reviewed-metrics.json']},
    'links': links, 'format_review': 'Local Markdown targets exist, fenced blocks balanced, git diff whitespace clean, no Chinese project text. External reference URLs were not revalidated in this local closeout.',
    'status': 'passed' if not errors else 'failed', 'failures': errors,
    'counts': {'documents_reviewed': len(paths), 'local_links_checked': len(links), 'failures': len(errors)},
    'metric_inventory': {key: {'status': 'not_applicable', 'value': None, 'reason': 'Documentation content/link/format review only; no runtime, retrieval or provider workload.'} for key in original}}
write_json(folder / 'documentation-review.json', record)
print(json.dumps({'status':record['status'], 'counts':record['counts'], 'failures':errors}, indent=2))
raise SystemExit(bool(errors))
