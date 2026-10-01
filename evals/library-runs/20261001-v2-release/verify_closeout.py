"""Review new documentation, final artifacts, credential hygiene and release boundaries."""
import hashlib,json,re,subprocess
from pathlib import Path
from urllib.parse import unquote
ROOT=Path(__file__).parent;REPO=Path.cwd()
read=lambda p:json.loads(p.read_text())
changed=subprocess.check_output(['git','diff','--name-only'],text=True).splitlines()
untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],text=True).splitlines()
paths=[Path(p) for p in sorted(set(changed+untracked)) if Path(p).is_file()]
markdown=[p for p in paths if p.suffix=='.md'];links=[];failures=[]
for p in markdown:
 text=p.read_text()
 if re.search('[\u4e00-\u9fff]',text):failures.append(f'Non-English project text: {p}')
 if text.count('```')%2:failures.append(f'Unbalanced code fence: {p}')
 for label,target in re.findall(r'\[([^\]]*)\]\(([^)]+)\)',text):
  target=target.strip('<>').split(' "')[0]
  if target.startswith(('http:','https:','mailto:','#')):continue
  destination=(p.parent/unquote(target.split('#')[0])).resolve();links.append({'from':str(p),'target':target,'exists':destination.exists()})
  if not destination.exists():failures.append(f'Broken local link: {p}: {target}')
m=read(ROOT/'measurement-final.json');assert len(m['cohorts'])==6
from record_check import METRICS
for cohort in m['cohorts'].values():assert set(cohort['metric_inventory'])==set(METRICS)
assert read(ROOT/'review.json')['summary']['case_gate']['passed']==6
assert read(ROOT/'heldout-review.json')['case_passes']==5
assert read(ROOT/'dependency-review.json')['after']['gate_passed']
assert read(ROOT/'backend-final-retry.json')['exit_code']==0
assert read(ROOT/'frontend-final.json')['exit_code']==0
assert read(ROOT/'browser-regressions.json')['exit_code']==0
assert read(ROOT/'build-final.json')['exit_code']==0
assert len(read(ROOT/'browser2-result.json')['checks'])==8
assert read(ROOT/'lifecycle-completion.json')['checks']==9
assert read(ROOT/'server-stop.json')['ownership_released']
freeze=read(ROOT/'heldout-execution-freeze.json')
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in freeze['product_hashes'].items())
assert hashlib.sha256(Path('evals/materials/pdf-v2-closeout-heldout/protocol.json').read_bytes()).hexdigest()==freeze['protocol_sha256']
assert hashlib.sha256(Path('.env').read_bytes()).hexdigest()==read(ROOT/'preparation.json')['env_sha256']
assert subprocess.run(['git','check-ignore','.env'],capture_output=True).returncode==0
assert '.env' not in subprocess.check_output(['git','ls-files'],text=True).splitlines()
assert subprocess.check_output(['git','branch','--show-current'],text=True).strip()=='v2'
assert not any('Quenwick' in p.read_text() for p in Path('knowledgebase').rglob('*.py'))
secret_pattern=re.compile(rb'sk-(?:proj-)?[A-Za-z0-9_-]{24,}')
findings=[str(p) for p in paths if p.suffix in ['.py','.json','.jsonl','.md','.log','.har','.cjs'] and secret_pattern.search(p.read_bytes())]
assert not findings, 'Potential secret material found; filenames only: '+repr(findings)
# Authored code/docs only: raw third-party outputs may retain trailing whitespace.
authored=[str(p) for p in paths if p.suffix in ['.py','.cjs','.md','.ts','.tsx']]
r=subprocess.run(['git','diff','--check','--',*authored],capture_output=True,text=True);assert r.returncode==0,r.stdout
result={'reviewer':'Codex','markdown_files':len(markdown),'local_links_checked':len(links),'link_failures':failures,'complete_metric_cohorts':6,'product_hashes_match_heldout_freeze':True,'heldout_protocol_unchanged':True,'env_unchanged_and_ignored':True,'credential_scan_findings':0,'no_fixture_target_in_product':True,'branch':'v2','merge_performed':False,'links':links,'format_check_passed':True}
with (ROOT/'artifact-review.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
assert not failures,failures
print(f'{len(markdown)} documentation files and {len(links)} local links reviewed; all final gates and six complete metric inventories verified; no secret findings.')
