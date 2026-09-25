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
    command = ['uv', 'run', '--locked', 'python', '-m', 'pytest', *args]
    target = DIRECTORY / name
    if target.with_suffix('.log').exists():
        raise SystemExit('Use a new record name; historical outputs are append-only.')
    state, start, started_at = git_state(), perf_counter(), timestamp()
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
