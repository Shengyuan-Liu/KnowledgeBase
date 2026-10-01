"""Append final accounting after browser work and asynchronous server shutdown."""
from pathlib import Path
import json
ROOT=Path(__file__).parent
read=lambda n:json.loads((ROOT/n).read_text())
m=read('measurement.json');obs=[json.loads(l) for l in (ROOT/'server-observations.jsonl').read_text().splitlines()]
query=next(o for o in obs if o['kind']=='sdk_start' and o['request']=='unlabeled' and o['api']=='embeddings' and o['input']['input']==['Which laboratory was assigned to Project Juniper in "lifecycle.pdf"?'])
end=next(o for o in obs if o.get('call_id')==query['call_id'] and o['kind']=='sdk_complete');u=end['result']['usage'];totals=m['total_provider_work']['usage_by_role']
for role,sign in [('ingestion_embedding',-1),('query_embedding',1)]:
 totals[role]['calls']+=sign;totals[role]['input_tokens']+=sign*u['prompt_tokens'];totals[role]['total_tokens']+=sign*u['total_tokens']
m['total_provider_work']['note']='126 unique terminal calls; reused D outcomes counted once. Includes 4 shadow assessments, 5 document-embedding calls (2 held-out PDFs, 3 UI uploads), and 56 query embeddings. The lifecycle query is identified by its exact raw input; ingestion and query roles are no longer grouped under the unlabeled browser request.'
m['correction_to_intermediate']='measurement.json initially grouped all four unlabeled browser embedding calls as ingestion. This final record moves the one question embedding to query_embedding; no total usage or quality score changes.'
m['ingestion_and_index']['final_index']=read('final-index-check-final.json');m['ingestion_and_index']['shutdown']=read('server-stop.json')
m['browser']={'real_saved_answer_checks':read('browser2-result.json'),'lifecycle':read('lifecycle-completion.json'),'failed_harness_attempts':['browser.json: hidden duplicate quote selected; retry limits to visible elements','lifecycle.json: final GET lacked a base URL; read-only completion uses absolute route','final-index-stop.json: process command used relative path; identity comparison corrected','final-index-stop-retry.json: listening socket closed before data lock released; later read-only confirmation passes'],'provider_accounting_note':'The first read-only browser pass overlapped 2 held-out ingestion calls. HAR contains only browser GET requests, so those are not UI-generated answer calls. Final browser replay issued no additional provider calls.','visual_review':'Codex inspected original finance pages 7/8, desktop/mobile controls, mobile dependency quote trace and physical lecture page 35. Full-page fit on a narrow screen is small; no zoom/readability claim.'}
m['offline_checks']={n:read(n+'.json') for n in ['backend-final','backend-final-retry','frontend-final','build-final','browser-regressions']}
with (ROOT/'measurement-final.json').open('x') as f:json.dump(m,f,indent=2);f.write('\n')
print('Final 20-metric inventories and unique provider/lifecycle accounting retained.')
