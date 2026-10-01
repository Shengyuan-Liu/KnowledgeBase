"""Retain the Codex review of expected facts and actual cited excerpts."""
import json
from pathlib import Path
ROOT=Path(__file__).parent
refs=json.loads(Path('evals/materials/pdf-v2-candidate-20261001/references.json').read_text())
facts={f['id']:f for f in refs['facts']}
for directory,final in [(ROOT.parent/'20261001-v2-closeout-matched',False),(ROOT,True)]:
 rows=[]
 for case in refs['cases']:
  raw=json.loads((directory/(case['case_id']+'-planned.json')).read_text())
  sources=raw['answer']['sources'];answer=raw['answer']['answer'];points=[]
  for f in case['fact_ids']:
   unsupported=not final and f in {'quarter_gaap','annual_gaap','annual_nongaap','income_units'}
   ids=([1,2] if f.startswith('rag_') else [1,3] if f=='retriever_bridge' and case['answerability']=='partial' else [1] if f=='retriever_bridge' or f.startswith('overfitting') else [2,5] if f.startswith('negative_') and final else [2] if f.startswith('negative_') else [2,4] if f=='quarter_nongaap' and not final else [2])
   ids=[i for i in ids if any(s['source_id']==i for s in sources)]
   points.append({'fact_id':f,'expected':facts[f]['expected'],'correct':True,'complete':True,'faithful':not unsupported,'citation_supported':not unsupported,'citation_covered':not unsupported,'supplied_semantic_evidence':not unsupported,'citation_ids':ids,'review': 'Source 2 contains numeric rows on page 8 but no periods or units; the annual/GAAP qualification is unsupported even though numbers match the original. Source 4 only establishes quarterly non-GAAP.' if unsupported else 'Exact cited source text and original page support this fact. For the repaired financial answer, Source 2 includes original page-7 period headers and units with page-8 values; supplements retain original offsets.'})
  extra=[]
  if not final and case['answerability']=='partial':
   extra=[{'claim':'RAG jointly trains retriever and generator.','citation_ids':[1,3],'faithful':True,'citation_supported':True,'citation_covered':True,'review':'Source 3 explicitly says both generator and retriever are jointly learned.'}]
  rows.append({'case_id':case['case_id'],'status':raw['status'],'answer':answer,'answerability':case['answerability'],'passed':final or case['case_id']!='income-period-basis','expected_points':points,'additional_claims':extra,'gap_disclosure_passed':True,'relevant':True,'source_artifact':case['case_id']+'-planned.json','review_note':'Repeated assertions counted once per atomic expected fact. The final granularity wording is redundant but supported. DPR per-question negative wording matches its training discussion. A claim-free refusal has no citation denominator.'})
 total=sum(len(x['expected_points']) for x in rows);extra=sum(len(x['additional_claims']) for x in rows)
 supported=sum(p['faithful'] for r in rows for p in r['expected_points'])
 summary={'case_gate':{'passed':sum(r['passed'] for r in rows),'total':6,'required':6,'accepted':final},'correctness':{'correct':total,'expected':13},'completeness':{'complete':total,'expected':13},'semantic_final_evidence_coverage':{'covered':supported,'expected':13},'faithfulness':{'supported':supported+extra,'claims':total+extra},'citation_support':{'supported':supported+extra,'cited_claims':total+extra},'citation_coverage':{'covered':supported+extra,'citation_required_claims':total+extra},'relevance':{'relevant':6,'total':6},'abstention':{'appropriate_full':{'passed':1,'total':1},'incorrect_full_on_fully_answerable':{'count':0,'total':4},'partial_gap_disclosure':{'passed':2,'total':2},'partial_supported_bridge':{'delivered':1,'total':1}}}
 with (directory/'review.json').open('x') as f:json.dump({'reviewer':'Codex model, not human','method':'Original-page and exact supplied-excerpt review; no paid judge. Expected facts scored separately from faithfulness/citation support. Valid IDs alone do not establish support.','summary':summary,'cases':rows},f,indent=2);f.write('\n')
 # Restrict timing/usage diagnostics to the six matched requests, even as later runs append SDK observations.
 source=(directory/'analyze.py').read_text().replace("    rows, timings = [], defaultdict(list)","    observations = [o for o in observations if o['request'] in {c['id'] + '-planned' for c in frozen['cases']}]\n    rows, timings = [], defaultdict(list)")
 scope={'__name__':'review_diagnostics','__file__':str(directory/'analyze.py')};exec(compile(source,str(directory/'analyze.py'),'exec'),scope);scope['analyze']()
print('Two complete matched reviews retained, including the 5/6 failed intermediate citation gate.')
