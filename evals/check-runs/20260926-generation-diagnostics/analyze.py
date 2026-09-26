"""Append a diagnosis of retained calls and host power events; no API requests."""
from datetime import datetime
import json
from pathlib import Path
import re
from evals.evaluate import digest, git_state, read_jsonl, timestamp, write_json

DIR = Path(__file__).parent
BASE = Path('evals/library-runs/20260925-document-representation')
if __name__ == '__main__':
    assert not (DIR/'diagnosis.json').exists()
    calls = [c for c in read_jsonl(BASE/'calls.jsonl') if c['stage'] == 'generation']
    power = []
    for line in (DIR/'power-events.log').read_text().splitlines():
        match = re.match(r'^(2026-09-25 17:\d\d:\d\d -0400) (Sleep|Wake|DarkWake)\s{2,}(.*)', line)
        if match:
            power.append({'at':datetime.strptime(match[1], '%Y-%m-%d %H:%M:%S %z').isoformat(), 'event':match[2], 'detail':match[3].strip()})
    rows = []
    for i,c in enumerate(calls):
        started = datetime.strptime(c['call_id'].split('-')[0], '%Y%m%dT%H%M%SZ').replace(tzinfo=datetime.fromisoformat('2026-09-25T00:00:00+00:00').tzinfo)
        times = [0] + [d['seconds'] for d in c['deltas']] + [c['seconds']]
        gap,index = max((b-a,i) for i,(a,b) in enumerate(zip(times,times[1:])))
        sleep = [p for p in power if p['event'] == 'Sleep' and abs((datetime.fromisoformat(p['at'])-started).total_seconds()) <= 1]
        rows.append({'case_id':c['case_id'],'call_id':c['call_id'],'status':c['status'],
            'generation_seconds':c['seconds'],'first_delta_seconds':times[1],
            'largest_observed_gap_seconds':gap, 'gap_after_delta_count':index,
            'last_delta_seconds':times[-2], 'sleep_within_one_second_of_call_id_timestamp':sleep})
    inventory = json.loads((DIR/'scoped-1.json').read_text())['metric_inventory']
    for key in inventory:
        inventory[key] = {'status':'not_applicable','value':None,'reason':'Read-only diagnosis of retained observations; no new RAG, provider or performance workload. Original full inventory remains linked.'}
    write_json(DIR/'diagnosis.json', {'recorded_at':timestamp(),'git':git_state(),
        'commands':['pmset -g log (filtered to 2026-09-25 17:08-17:32 -0400 sleep/wake records)', 'uv run python -m evals.check-runs.20260926-generation-diagnostics.analyze'],
        'source_hashes':{str(p):digest(p.read_bytes()) for p in [BASE/'calls.jsonl',BASE/'answers.jsonl',BASE/'run.json',DIR/'power-events.log']},
        'calls':rows,'power_events':power,'metric_inventory':inventory,
        'conclusions':['All three slow/error generations start within one second of recorded host sleep.',
            'Strong evidence that host suspension confounds this run; cannot assign delays solely to the upstream provider.',
            'Active durations and UTC timestamps differ; historical per-event wall elapsed was not recorded.',
            'Read timeout occurs 60.003 seconds after the last recorded delta, matching configured timeout; no auth/quota error evidence.',
            'Preserve failed results, add both clocks to future records, and temporarily prevent idle/system sleep during bounded acceptance.']})
    print('Retained diagnosis for',len(rows),'generation calls and',len(power),'sleep/wake events.')
