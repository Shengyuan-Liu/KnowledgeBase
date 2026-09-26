"""Compare frozen judge runs without changing scores or historical artifacts."""
import json
from pathlib import Path

from evals import metrics
from evals.evaluate import digest, read_jsonl, write_json

HERE = Path(__file__).parent
BASE = Path('evals/calibration-runs')
OLD_CAL = BASE / '20260924T193931Z-14f32e71-claim-inventory-v10'
NEW_CAL = BASE / '20260924T195838Z-1b2656db-claim-inventory-v11'
OLD_REAL = BASE / '20260924T194004Z-1a80463c-saved-answers-high'
NEW_REAL = BASE / '20260924T200002Z-de0c50b4-saved-answers-high'


def read(path):
    return json.loads(path.read_text())


def stats(directory):
    rows = read_jsonl(directory / 'reviews.jsonl')
    calls = [c for r in rows for c in r['calls']]
    usages = [c['usage'] for c in calls if c.get('usage')]
    def timing(values):
        result = metrics.timing(values)
        result.update(method='All completed attempts, including errors/pending; median P50, nearest-rank P95; worker queue excluded.',
                      artifact=str(directory / 'reviews.jsonl'))
        return result
    return {'n':len(rows), 'valid':sum(r['status']=='ok' for r in rows),
        'pending':[r['case_id'] for r in rows if r['status']!='ok'],
        'judge_seconds':timing([r['seconds'] for r in rows]),
        'stage_seconds':{stage:timing([r['calls'][i]['seconds'] for r in rows if len(r['calls'])>i])
            for i,stage in enumerate(('inventory','inventory_audit','assessment'))},
        'calls':len(calls), 'usage_calls':len(usages),
        'tokens':{k:sum(u[k] for u in usages) for k in ('input_tokens','output_tokens','total_tokens')},
        'api_errors':sum(c['status']!='ok' for c in calls),
        'timeouts':sum('Timeout' in c.get('error_type','') for c in calls), 'retries':0,
        'method':'All attempts, including errors/pending; mean, median P50, nearest-rank P95; worker queue excluded.',
        'cost':metrics.missing('Billed dollars are not exposed in provider responses.'), 'artifact':str(directory)}


if __name__ == '__main__':
    if (HERE / 'comparison.json').exists():
        raise SystemExit('Comparison already exists; preserve append-only artifacts.')
    assert (OLD_CAL/'cases.json').read_bytes() == (NEW_CAL/'cases.json').read_bytes()
    assert (OLD_REAL/'answers.jsonl').read_bytes() == (NEW_REAL/'answers.jsonl').read_bytes()
    before = {r['case_id']:r for r in read_jsonl(OLD_REAL/'reviews.jsonl')}
    answers = {r['case_id']:r for r in read_jsonl(NEW_REAL/'answers.jsonl')}
    cases = {c['id']:c for c in read(NEW_REAL/'cases.json')}
    changes, inspection = [], []
    for row in read_jsonl(NEW_REAL/'reviews.jsonl'):
        identity = row['case_id']
        oldq, newq = metrics.quality(before[identity], cases[identity]), metrics.quality(row, cases[identity])
        changes.append({'case_id':identity, 'before_status':before[identity]['status'], 'after_status':row['status'],
                        'before_quality':oldq, 'after_quality':newq})
        inspection.append({'case_id':identity, 'answer':answers[identity]['answer'],
            'status':row['status'], 'inventory':row.get('inventory'), 'audit':row.get('inventory_audit'),
            'negative_claims':[c for c in row.get('assessment',{}).get('claims',[]) if c['verdict']!='supported'],
            'non_full_points':[p for p in row.get('assessment',{}).get('points',[]) if p['correctness']!=2],
            'claims':row.get('claims'), 'assessment':row.get('assessment')})
    result = {'calibration':{'before':stats(OLD_CAL),'after':stats(NEW_CAL),
        'before_checks':read(OLD_CAL/'checks.json'),'after_checks':read(NEW_CAL/'checks.json')},
        'saved_answers':{'before':stats(OLD_REAL),'after':stats(NEW_REAL),'per_case':changes},
        'same_calibration_bytes':True,'same_answer_bytes':True,
        'answer_sha256':digest((NEW_REAL/'answers.jsonl').read_bytes()),
        'limits':['Same answers and evidence; score changes measure judge behavior, not RAG improvement.',
            'Schema and prompts changed together. Small development set; not human ground truth or held-out accuracy.',
            'One stochastic pass per protocol. Timings are descriptive; provider load/cache is uncontrolled.',
            'Only judge timing and usage are newly measured; RAG retrieval, latency and generation usage are reused.']}
    write_json(HERE/'comparison.json',result)
    write_json(HERE/'saved-answer-inspection.json',inspection)
    print(json.dumps({k:{side:v[side] for side in ('before','after')} for k,v in result.items()
        if k in ('calibration','saved_answers')},indent=2))
