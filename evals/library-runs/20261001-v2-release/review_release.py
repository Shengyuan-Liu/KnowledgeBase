"""Record claim/point review separately from automatic ranking and timing diagnostics."""
import json,re
from pathlib import Path
ROOT=Path(__file__).parent
read=lambda p:json.loads(p.read_text())
def write(name,data):
 with (ROOT/name).open('x') as f:json.dump(data,f,indent=2);f.write('\n')
refs=read(Path('evals/materials/pdf-v2-candidate-20261001/references.json'))
bycase={c['case_id']:c for c in refs['cases']}

# The held-out answers and their exact cited sources were inspected against original pages.
protocol=read(Path('evals/materials/pdf-v2-closeout-heldout/protocol.json'))
notes={
'bert-sizes':'Cited sources contain both Base (12 layers, 110M) and Large (24 layers, 340M), matching original physical page 3.',
'bert-objectives':'Cited page-4 prose defines MLM masking/prediction and NSP actual-next versus random sentences. Both added explanations are supported; no diagram is needed.',
 'transformer-training':'Source 1 on physical page 8 states 3.5 days and 8 P100 GPUs; Source 4 additionally states NVIDIA and 300,000 steps on physical page 7.',
 'transformer-energy-partial':'Source 1 supports 3.5 days and 8 P100 GPUs; Source 2 labels training cost as FLOPs. No energy amount is invented, and the absence claim is scoped to supplied excerpts.',
 'bert-moon-result':'Claim-free refusal; neither the selected paper nor final excerpts contain the named nonexistent benchmark.'}
held=[]
for case in protocol['questions']:
 r=read(ROOT/'heldout'/f"{case['id']}--D.json");assert r['status']=='completed';a=r['answer'];assert not a['citation_check']['invalid_source_ids']
 points=[{'fact_id':f,'correct':True,'complete':True,'supplied_semantic_evidence':True,'faithful':True,'citation_supported':True,'citation_covered':True} for f in case['facts']]
 extra=[]
 if case['id']=='bert-objectives':extra=[{'claim':x,'faithful':True,'citation_supported':True,'citation_covered':True,'citation_ids':[1,3]} for x in ['MLM masks input tokens and predicts them.','NSP distinguishes the actual next sentence from a random sentence.']]
 if case['id']=='transformer-energy-partial':extra=[{'claim':x,'faithful':True,'citation_supported':True,'citation_covered':True,'citation_ids':ids} for x,ids in [('Training used 8 P100 GPUs.',[1,3]),('The provided cost table reports FLOPs.',[2])]]
 held.append({'case_id':case['id'],'answer':a['answer'],'passed':True,'expected_points':points,'additional_claims':extra,'gaps':case.get('gaps',[]),'gap_disclosure_correct':True,'review':notes[case['id']],'invalid_citation_ids':a['citation_check']['invalid_source_ids'],'first_delta':r['first_answer_delta_seconds'],'completion':r['complete_response_seconds'],'sources_file':f"heldout/{case['id']}--D.json"})
assert max(r['first_delta'] for r in held)<=protocol['gate']['per_request_first_delta_seconds_max']
assert max(r['completion'] for r in held)<=protocol['gate']['per_request_complete_seconds_max']
write('heldout-review.json',{'reviewer':'Codex model, not independent human','rubric':'Frozen material protocol; every expected point and substantive additional assertion checked against supplied excerpts and original pages. Duplicate restatements counted once.','case_passes':5,'case_total':5,'correct_positive_instances':10,'positive_instances':10,'claims_supported':14,'claims_total':14,'citations_supported':14,'citations_required':14,'proper_refusal':{'passed':1,'total':1},'partial_gap':{'passed':1,'total':1},'incorrect_full_refusal':{'count':0,'fully_answerable':3},'cases':held,'limits':'New-to-project corpus, small one-pass sample, public papers potentially present in model pretraining. No independent human or statistical validation.'})

ablation=[]
for arm in 'ABCD':
 for case in read(ROOT/'ablation-protocol.json')['questions']:
  r=read(ROOT/'ablation'/f"{case['id']}--{arm}.json");a=r['answer'];name=case['id'];facts=bycase[name]['fact_ids'] if name in bycase else ['lab_bridge','lab_interval']
  points=[]
  for fact in facts:
   correct=not(arm=='A' and name=='income-period-basis' and fact=='annual_nongaap')
   points.append({'fact_id':fact,'correct':correct,'complete':correct,'faithful':correct,'citation_supported':correct,'citation_covered':correct,'supplied_semantic_evidence':True,'note':'Contradictory 82,722 / 86,789 / final refusal; do not select the convenient intermediate number as a correct final answer.' if not correct else 'Supported original fact; A GAAP income uses correctly cited gross-profit and expense operands. The correct annual non-GAAP value is also derivable from its supplied operands, although A fails to deliver a consistent answer.'})
  extras=[]
  if name=='retriever-training-restricted' and arm in 'ABC':
   extras=[{'claim':f'DPR retrieval supervision uses {dataset}.','faithful':True,'citation_supported':True,'citation_covered':True} for dataset in ['Natural Questions','TriviaQA']]
   if arm=='A':extras += [{'claim':x,'faithful':False,'citation_supported':False,'citation_covered':False} for x in ['DPR best-model training uses in-batch negatives.','DPR best-model training uses BM25 negatives.']]
  if name=='income-period-basis' and arm=='A':
   extras=[
    {'claim':'GAAP income is obtained by the stated gross-profit minus operating-expense calculations.','faithful':True,'citation_supported':True,'citation_covered':True,'note':'Both operands and period headers occur in Source 2; arithmetic is correct.'},
    {'claim':'Full-year non-GAAP operating expenses are 15,783 million.','faithful':False,'citation_supported':False,'citation_covered':False,'note':'Unsupported intermediate amount, not erased by subsequent correction.'},
    {'claim':'The mixed Q4 FY25, Q3 FY25 and Q4 FY24 quarterly values establish the annual expense amount.','faithful':False,'citation_supported':False,'citation_covered':False,'note':'Periods are not a full-year sum.'},
    {'claim':'16,405 minus 4,559 minus 130 gives 11,716 million non-GAAP operating expenses.','faithful':True,'citation_supported':False,'citation_covered':False,'note':'Source 2 has these operands, but this separate calculation has no local citation.'},
    {'claim':'98,505 minus 11,716 gives 86,789 million non-GAAP operating income.','faithful':True,'citation_supported':False,'citation_covered':False,'note':'Derivable from supplied operands, without a local citation; final answer later refuses this value.'}]
  invalid=a['citation_check']['invalid_source_ids'];gap_ok=not(arm=='A' and name=='retriever-training-restricted');passed=all(p['correct'] for p in points) and gap_ok and not invalid and all(e['faithful'] and e['citation_covered'] for e in extras)
  planning=a['retrieval'].get('planning') or {};hops=planning.get('hops') or {}
  ablation.append({'case_id':name,'arm':arm,'passed':passed,'answer':a['answer'],'expected_points':points,'additional_claims':extras,'invalid_citation_ids':invalid,'gap_disclosure_correct':gap_ok,'relevant':not(arm=='A' and name in ['income-period-basis','retriever-training-restricted']),'dependency_executed':any(d['status']=='executed' for d in hops.get('dependencies',[])),'round_count':len(hops.get('rounds',[])) or 1,'review':'No model repair or answer trimming. All contradictory drafts, copied bibliography marker [26], unsupported details, and final refusals count in the result.'})
shadow=[]
for p in sorted((ROOT/'ablation').glob('*--shadow.json')):
 data=read(p)['result'];assessment=data['assessment'];shadow.append({'artifact':str(p.relative_to(ROOT)),'requirement_statuses':[{'description':r['description'],'status':r['status'],'reviewed_correct':True} for r in assessment['requirements']],'proposed_queries':len(assessment['queries']),'searches_executed':0,'review':'Available requested facts supported; restricted DPR recipe missing. Unexecuted proposal is not a coverage improvement.'})
write('ablation-review.json',{'reviewer':'Codex model, not human','method':'Expected-point scoring plus all substantive additional claim groups; duplicate restatements grouped, contradictory drafts retained. Citation validity separate from semantic support. No independent review.','cases':ablation,'case_gate_by_arm':{arm:{'passed':sum(r['passed'] for r in ablation if r['arm']==arm),'total':4} for arm in 'ABCD'},'shadow_C':shadow,'interpretation':'D passes 4/4 scoped cases; A fails missing-evidence/financial answer consistency, B/C copy an invalid bibliography citation. This sample does not demonstrate a coverage gain from supplementary search: C already has the answerable evidence and its missing restricted fact is outside scope.'})

before=read(ROOT.parent/'20261001-v2-closeout-matched/dependency/unknown-laboratory-planned.json')
after=read(ROOT/'dependency/unknown-laboratory--D.json')
hops=after['answer']['retrieval']['planning']['hops'];state=hops['dependencies'][0]
assert state['status']=='executed' and state['target']=='Quenwick Laboratory'
assert state['references'][0]['quote']=='Project Juniper was assigned to Quenwick Laboratory.'
assert len(hops['rounds'])==2 and state['references_in_final_context']
write('dependency-review.json',{'reviewer':'Codex model','synthetic':True,'before':{'file':'../20261001-v2-closeout-matched/dependency/unknown-laboratory-planned.json','correct_facts':1,'expected_facts':2,'gate_passed':False,'reason':'Explicit identity was incorrectly classified missing because the final attribute was absent.'},'after':{'file':'dependency/unknown-laboratory--D.json','correct_facts':2,'expected_facts':2,'gate_passed':True,'trace':state,'rounds':2},'scope':'Same exact two PDF bytes and question; changed generic binding instructions and prerequisite query payload. No expected target supplied in request. The original RAG/DPR question remains independently searched; do not reclassify it as dependent.'})
print('Held-out 5/5; dependency 1/1; A-D gates recorded with all control-arm failures.')
