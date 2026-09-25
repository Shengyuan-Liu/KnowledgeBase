"""Audit supplemental provenance and qualify combined historical metrics."""
from copy import deepcopy
import json
from pathlib import Path
from evals import judge, metrics
from evals.evaluate import digest, read_jsonl, timestamp, write_json
DIR=Path(__file__).parent
ROOT=DIR.parent/'20260925-generation-citations'
FIRST=DIR.parent/'20260925-review-supplement'

if __name__=='__main__':
    originals={r['case_id']:r for r in read_jsonl(ROOT/'reviews.jsonl')}
    checks=[]
    assert (DIR/'answers.jsonl').read_bytes()==(ROOT/'answers.jsonl').read_bytes()
    checks.append('All 24 answer rows remain byte-identical to the generation comparison.')
    calls=[]
    for directory in (FIRST,DIR):
        for row in read_jsonl(directory/'supplemental-reviews.jsonl'):
            prior=originals[row['case_id']]
            call=row['calls'][0]
            assert len(row['calls'])==1
            assert call['messages']==prior['calls'][-1]['messages'] and call['schema']==prior['calls'][-1]['schema']
            assert row['inventory']==prior['inventory'] and row['claims']==prior['claims']
            assert row['protocol_sha256']==judge.protocol_hash()
            assert call['model']==prior['model'] and call['reasoning_effort']==prior['reasoning_effort']
            calls.append(call)
    checks.append('Three supplemental assessments reused exact original payloads/schema, inventory, answer and judge configuration.')
    assert len(read_jsonl(DIR/'calls.jsonl'))==len(read_jsonl(ROOT/'calls.jsonl'))+3
    checks.append('All original generation/judge attempts plus all three supplemental provider calls retained; aborted preflight made no provider call.')
    summary=deepcopy(json.loads((DIR/'after-all.json').read_text()))
    summary['metrics']['judge_seconds']=metrics.missing('Effective rows mix original three-stage reviews and assessment-only supplements. Use call timings and supplemental run wall times instead.')
    summary['metrics']['judge_reliability']['method']='Effective review state: 23 valid, one invalid after manual supplemental attempts. Original 2 timeouts and subsequent 2 invalid credits assessments remain in raw records.'
    write_json(DIR/'qualified-after-all.json',summary)
    usage={key:sum(c['usage'][key] for c in calls) for key in ('input_tokens','output_tokens','total_tokens')}
    write_json(DIR/'audit.json',{'timestamp':timestamp(),'checks':checks,'passed':len(checks),
        'incremental_assessment_calls':3,'incremental_usage':usage,'incremental_provider_latency':metrics.timing([c['seconds'] for c in calls]),
        'incremental_cost':metrics.missing('Actual provider billing unavailable; token counts do not establish billed cost.'),
        'outcome':{'effective_valid_reviews':23,'planned_reviews':24,'credits_status':'invalid','original_timeouts':2,'subsequent_invalid_assessments':2,'aborted_preflight_runs':1}})
    print(len(checks),'provenance checks passed; 23 valid reviews, one unresolved; incremental usage:',usage)
