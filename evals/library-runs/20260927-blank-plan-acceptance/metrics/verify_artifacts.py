"""Check reported results against frozen facts, trace records and local documents."""
from pathlib import Path
import json
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from record_check import METRICS

def read(path):return json.loads(path.read_text())
measurement=read(ROOT/'metrics/measurement.json')
for metrics in [*measurement['groups'].values(),measurement['shared_preparation']]:
    assert set(metrics)==set(METRICS)
    for metric in metrics.values():
        assert metric['status'] in {'measured','not_applicable','unavailable'}
        if metric['status']!='measured':assert metric['value'] is None and metric['reason']
assert all(gate['passed'] for gate in measurement['scoped_gates'].values())
assert measurement['end_to_end_point_delivery']['correct_points']==24
assert measurement['end_to_end_point_delivery']['intended_points']==24
assert measurement['independent_second_review']['status']=='unavailable'
assert measurement['unsupported_limitations']==[]
all_metrics=measurement['groups']['all']
assert all_metrics['Reliability']['value']['completed']==6
assert all_metrics['Reliability']['value']['errors']==0
assert all_metrics['Token usage and cost']['value']['sdk_calls_started']==27
assert all_metrics['Token usage and cost']['value']['billed_cost']['status']=='unavailable'
review=read(ROOT/'review/reviewed-cases.json')
assert sum(len(row['factual_claim_groups']) for row in review['rows'])==21
assert all(point['reference_correctness']==point['completeness']==1 for row in review['rows'] for point in row['points'])
assessments=read(ROOT/'review/assessment-reference-review.json')['rows']
requirements=[r for row in assessments for r in row['requirements']]
assert len(requirements)==14
missing=[r for r in requirements if r['requirement']['status']=='missing']
assert len(missing)==1 and missing[0]['requirement']['requirement_id']=='R5'
assert 'false missing-status' in missing[0]['manual_status_judgment']
assert 'no limitations' in missing[0]['requirement']['gap'].lower()
for row in review['rows']:
    if row['arm']=='planned':
        raw=read(ROOT/(row['case_id']+'-planned.json'))
        assert 'added_coverage_query' not in raw['answer']['retrieval']['planning']['planner']
assert read(ROOT/'run-integrity.json')['shutdown_verified']
assert read(ROOT/'run-integrity.json')['completed_requests']==6
paths=[ROOT/'README.md',ROOT/'protocol.md',Path('docs/v2/README.md'),Path('docs/planned-retrieval.md'),Path('docs/dependent-retrieval.md'),Path('evals/check-runs/20260927-blank-plan/README.md')]
links=0
for path in paths:
    text=path.read_text()
    assert not re.search(r'[\u4e00-\u9fff]',text)
    assert text.count('\n```')%2==0
    for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text):
        if not link.startswith('http'):
            assert (path.parent/link.split('#',1)[0]).resolve().exists(),(path,link)
            links+=1
subprocess.run(['git','diff','--check','--','knowledgebase','tests','docs',str(ROOT/'README.md'),str(ROOT/'metrics')+'/*.py',str(ROOT/'review')+'/*.py'],check=True)
print(f'Reviewed {len(paths)} English documents and {links} local links. Confirmed 6/6 completions, 24/24 requested points, 21/21 factual groups, full metric inventories, unavailable independent review/cost, and the separate R5 status defect. No provider calls.')
