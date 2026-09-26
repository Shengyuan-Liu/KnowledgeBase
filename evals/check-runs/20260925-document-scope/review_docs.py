"""Record the final content, local-link and formatting review without provider calls."""
import json
from pathlib import Path
import re
import subprocess
from time import perf_counter
from evals.evaluate import digest, git_state, timestamp, write_json

DIR = Path(__file__).parent
FILES = [Path(p) for p in (
    'README.md', 'docs/v1/README.md', 'docs/v1/merge-readiness.md',
    'docs/answer-grounding.md', 'docs/document-scope.md',
    'evals/check-runs/20260925-document-scope/README.md',
    'evals/library-runs/20260925-document-representation/README.md',
    'evals/library-runs/20260925-document-representation/REVIEW.md',
    'evals/library-runs/20260925-document-representation/METRICS.md',
    'evals/library-runs/20260925-scope-timeout-recovery/README.md',
    'evals/library-runs/20260925-scope-timeout-recovery/REVIEW.md',
    'evals/library-runs/20260925-scope-timeout-recovery/METRICS.md',
)]
if __name__ == '__main__':
    target = DIR/'final-doc-review-1.json'
    assert not target.exists()
    started_at, start = timestamp(), perf_counter()
    errors, links = [], []
    for path in FILES:
        text = path.read_text()
        if re.search(r'[\u3400-\u9fff]', text):
            errors.append(f'{path}: unexpected non-English CJK content')
        if sum(line.startswith('```') for line in text.splitlines()) % 2:
            errors.append(f'{path}: unbalanced code fence')
        for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)', text):
            if '://' in link or link.startswith('#'):
                continue
            dest = (path.parent/link.split('#')[0]).resolve()
            links.append({'file':str(path), 'target':link, 'exists':dest.exists()})
            if not dest.exists():
                errors.append(f'{path}: missing target {link}')
    diff = subprocess.run(['git','diff','--check'], capture_output=True, text=True)
    if diff.returncode:
        errors.append(diff.stdout + diff.stderr)
    inventory = json.loads((DIR/'final-artifact-audit-1.json').read_text())['metric_inventory']
    for key in inventory:
        inventory[key] = {'status':'not_applicable', 'value':None,
                          'reason':'Documentation/link/format review; no retrieval, generation, provider calls or performance workload.'}
    write_json(target, {'command':['uv','run','python','-m','evals.check-runs.20260925-document-scope.review_docs'],
        'started_at':started_at, 'finished_at':timestamp(), 'seconds':perf_counter()-start,
        'git':git_state(), 'scope':'New and updated acceptance/readiness docs; draft reporting wording only after seven artifact checks passed.',
        'reviewer':'Codex implementer',
        'content_review':['Claims checked against raw service/call timings and manual source review.',
            'First pass 10/11 service and 9/11 strict; combined 11/12 service and 10/11 distinct strict.',
            'Comparison missing frozen absence point preserved; no relaxation or semantic redraw.',
            'Timeout, slow completions, usage gaps, exact benchmark scope and no merge remain explicit.',
            'English content, local link targets and code fence balance checked; git diff whitespace checked.',
            'No held-out, independent-human or current live-browser claim. No new paid calls.'],
        'files':{str(p):digest(p.read_bytes()) for p in FILES}, 'local_links':links,
        'errors':errors, 'status':'passed' if not errors else 'failed', 'metric_inventory':inventory})
    print(f'Document review: {len(FILES)} files, {len(links)} local links, {len(errors)} errors.')
    for error in errors:
        print(error)
    raise SystemExit(bool(errors))
