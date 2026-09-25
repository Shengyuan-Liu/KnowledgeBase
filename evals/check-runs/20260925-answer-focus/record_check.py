"""Record offline checks with the complete measurement inventory."""
import json
from pathlib import Path
import re
import subprocess
import sys
from time import perf_counter

from evals.evaluate import git_state, timestamp, write_json

DIRECTORY = Path(__file__).parent

if __name__ == '__main__':
    name, *args = sys.argv[1:]
    command = args
    target = DIRECTORY / name
    if target.with_suffix('.log').exists():
        raise SystemExit('Use a new record name; historical outputs are append-only.')
    state, start, started_at = git_state(), perf_counter(), timestamp()
    from hashlib import sha256
    state['frontend_sha256'] = {str(p): sha256(p.read_bytes()).hexdigest()
        for p in sorted(Path('frontend/src').rglob('*')) if p.is_file()}
    result = subprocess.run(command, capture_output=True, text=True)
    output = result.stdout + result.stderr
    target.with_suffix('.log').write_text(output)
    inventory = json.loads(Path('evals/check-runs/20260924-judge-calibration/backend-6.json').read_text())['metric_inventory']
    write_json(target.with_suffix('.json'), {'command':command, 'git':state, 'started_at':started_at,
        'finished_at':timestamp(), 'seconds':perf_counter()-start, 'exit_code':result.returncode,
        'counts':{status:int(count) for count,status in re.findall(r'(\d+) (passed|failed|skipped|error)', output)},
        'failures_artifact':str(target.with_suffix('.log')), 'metric_inventory':inventory})
    print(output)
    raise SystemExit(result.returncode)
