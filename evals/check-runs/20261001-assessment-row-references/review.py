"""Review retained failures, frozen comparisons, tested code and documentation."""
from hashlib import sha256
import json
from pathlib import Path
import re

from knowledgebase.config import Settings
from record_check import METRICS

ROOT=Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT/name).read_text())


if __name__=='__main__':
    scoped=load('scoped-1.json')
    assert scoped['exit_code']==0 and scoped['counts']['passed']==161
    assert load('focused-1.json')['counts']==dict(passed=32,failed=1,skipped=0,error=0)
    assert load('baseline-probe.json')['baseline_already_differs_from_historical_context']
    assert load('baseline-probe.json')['baseline_user_message_equals_current']
    for path,digest in scoped['changed_and_tracked_file_hashes'].items():
        if path.startswith(('knowledgebase/','tests/')):
            assert sha256(Path(path).read_bytes()).hexdigest()==digest
    for path,digest in load('frozen-inputs.json')['files'].items():
        assert sha256(Path(path).read_bytes()).hexdigest()==digest
    print('Tested code and frozen inputs match; original focused failure and baseline confirmation preserved.')
    comparison=load('comparison.json')
    assert len(comparison['pairs'])==6
    assert [p['table_rows'] for p in comparison['pairs']]==[0,0,0,0,40,35]
    assert sum(p['marked_after'] for p in comparison['pairs'])==75
    assert sum(p['marked_before'] for p in comparison['pairs'])==0
    for p in comparison['pairs']:
        assert p['before_coverage']==p['after_coverage'] and all(p['after_coverage'].values())
        assert p['answer_context_tokens']<=4096
        assert p['after_assessment_tokens']<=8192 and p['after_answer_input_tokens']<=16384
        assert p['after_answer_input_tokens']-p['before_answer_input_tokens']==111
    for name in ['comparison.json','scoped-1.json','focused-1.json','replay-before.json','replay-after.json']:
        inventory=load(name)['metric_inventory']
        assert set(inventory)==set(METRICS)
        for metric in inventory.values():
            assert metric['status'] in {'measured','not_applicable','unavailable'}
            assert all(k in metric for k in ['value','unit','sample_count','population','method','aggregation','artifact'])
            assert (ROOT/metric['artifact']).exists()
            if metric['status']!='measured':
                assert metric['value'] is None and metric['reason']
    print('All 20 metric statuses/links, 75 row mappings, fact coverage and local input budgets verified.')
    for path in [ROOT/'README.md',Path('docs/evidence-sufficiency.md'),Path('docs/v2/README.md')]:
        content=path.read_text()
        assert not re.search('[\u4e00-\u9fff]',content)
        assert all(line.rstrip()==line for line in content.splitlines())
        for link in re.findall(r'\]\(([^)]+)\)',content):
            if not link.startswith(('https://','http://','#')):
                assert (path.parent/link.split('#')[0]).exists(),(path,link)
    assert '`evidence-sufficiency-v6`' in Path('docs/evidence-sufficiency.md').read_text()
    secret=Settings().openai_api_key.encode()
    assert secret
    for p in ROOT.rglob('*'):
        if p.is_file() and p.suffix in {'.py','.md','.json','.log'}:
            assert secret not in p.read_bytes()
    print('English docs, links, formatting, v6 prompt version, offline scope and credential exclusion reviewed.')
    print('3 passed')
