"""Check final evidence inventory, explicit failures and local documentation links."""
from pathlib import Path
import json
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from record_check import METRICS

def read(path):return json.loads(path.read_text())
measurement=read(ROOT/'metrics/measurement-2.json')
prior=read(ROOT/'metrics/measurement.json')
for arm in ['single','planned','all']:
    metrics=measurement['groups'][arm]
    assert set(metrics)==set(METRICS)
    for name,metric in metrics.items():
        assert metric['status'] in {'measured','not_applicable','unavailable'}
        if metric['status'] != 'measured':assert metric['value'] is None and metric['reason']
        assert metric['value']==prior['groups'][arm][name]['value'], (arm,name)
assert set(measurement['shared_preparation'])==set(METRICS)
all_metrics=measurement['groups']['all']
assert all_metrics['Reliability']['value']['completed']==5
assert all_metrics['Reliability']['value']['errors']==1
assert all_metrics['Answer correctness']['point_count']==21
assert all_metrics['Answer correctness']['unavailable_point_count']==3
assert measurement['end_to_end_point_delivery']['correct_points']==19
assert measurement['end_to_end_point_delivery']['intended_points']==24
assert not measurement['scoped_gates']['six_requests_complete']['passed']
assert not measurement['scoped_gates']['requested_points_correct_and_complete']['passed']
assert measurement['independent_second_review']['status']=='unavailable'
assert len(measurement['unsupported_limitations'])==1
assert len(measurement['unsupported_limitations'][0]['points'])==2
usage=all_metrics['Token usage and cost']['value']
assert usage['sdk_calls_started']==22 and usage['billed_cost']['status']=='unavailable'
assert read(ROOT/'metrics/planner-failure-replay.json')['reproduced']
assert read(ROOT/'run-integrity.json')['shutdown_verified']
assert read(ROOT/'measurement.json')['canonical_measurement']=='metrics/measurement-2.json'
review=read(ROOT/'review/reviewed-cases.json')
assert sum(len(r['factual_claim_groups']) for r in review['rows'])==19
failed=next(r for r in review['rows'] if r['answer_status']=='error')
assert all(p['reference_correctness'] is None for p in failed['points'])
assert failed['incorrect_abstention'] is None
assert sum(len(a['requirements']) for a in read(ROOT/'review/assessment-reference-review.json')['rows'])==9
paths=[ROOT/'README.md',ROOT/'protocol.md',Path('docs/v2/README.md'),Path('evals/check-runs/20260927-table-cell-context/README.md')]
links=0
for path in paths:
    text=path.read_text()
    assert not re.search(r'[\u4e00-\u9fff]',text)
    assert text.count('\n```')%2==0
    for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text):
        if not link.startswith('http'):
            assert (path.parent/link.split('#',1)[0]).resolve().exists(), (path,link)
            links+=1
subprocess.run(['git','diff','--check','--','knowledgebase','tests','docs',str(ROOT/'metrics'),str(ROOT/'review'),str(ROOT/'README.md')],check=True)
print(f'Reviewed {len(paths)} English documents and {links} local links. Full metric inventories, unchanged numeric measurements, 5/6 completions, 19/24 delivered points, unavailable failure scores, unsupported blank limitation, reviewer limitation, provenance and shutdown are explicit. No provider calls.')
