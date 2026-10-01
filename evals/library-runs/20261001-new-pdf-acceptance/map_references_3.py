"""Map frozen original-page quotes to canonical spans before any answer requests."""
import json
from pathlib import Path
from prepare import ROOT, MATERIAL, write

def compact(text):
    pairs=[(c.casefold(),i) for i,c in enumerate(text) if not c.isspace()]
    return ''.join(c for c,i in pairs),[i for c,i in pairs]

snapshot=json.loads((ROOT/'index-snapshot.json').read_text())
reference=json.loads((MATERIAL/'references.json').read_text())
labels={};facts={}
for fact in reference['facts']:
    ref=fact['evidence'][0];document=next(d for d in snapshot['files'] if d['file']['file_name']==ref['file'])
    needle,_=compact(ref['normalized_quote']);matches=[]
    for block in document['extraction']['blocks']:
        if not any(r['page_index']+1==ref['physical_page'] for r in block['regions']):continue
        haystack,positions=compact(block['text']);start=0
        while (start:=haystack.find(needle,start))>=0:
            a,b=positions[start],positions[start+len(needle)-1]+1
            matches.append(dict(file_id=document['file']['file_id'],start=block['start_offset']+a,end=block['start_offset']+b,text=block['text'][a:b],source_ref=block['source_ref']))
            start+=len(needle)
    anchors=[dict(anchor=matches[0]['text'] if matches else ref['normalized_quote'],spans=[{k:m[k] for k in ['file_id','start','end']} for m in matches])]
    labels[fact['id']]=dict(fact=fact,anchors=anchors,fully_mapped=bool(matches),canonical_matches=matches,physical_page=ref['physical_page'],normalization='Whitespace removed and casefolded only; original offsets preserved.',ambiguity='Repeated identical unit notes on the same page are equivalent for this unit fact.' if len(matches)>1 else None)
    facts[fact['id']]=dict(file=ref['file'],physical_pages=[ref['physical_page']],anchors=[ref['normalized_quote']],expected=fact['expected'])
write('frozen-labels.json',labels)
questions=json.loads((MATERIAL/'questions.json').read_text())['questions']
cases=[]
for q in questions:
    ref=next(c for c in reference['cases'] if c['case_id']==q['id'])
    cases.append(dict(**q,expected_fact_ids=ref['fact_ids'],answerability=ref['answerability'],gap_ids=ref['gap_ids']))
write('frozen-cases.json',dict(cases=cases,facts=facts,corpus=json.loads((MATERIAL/'manifest.json').read_text())['files'],purpose='Analysis only; run.py reads request-only sealed questions instead.'))
write('mapping-freeze.json',dict(mapped=sum(l['fully_mapped'] for l in labels.values()),expected=len(labels),answer_calls_before_mapping=0,source='references.json frozen before ingestion',missing=[k for k,v in labels.items() if not v['fully_mapped']]))
print(f'{sum(l["fully_mapped"] for l in labels.values())}/{len(labels)} facts mapped; missing mappings retained as failures, never removed from denominator.')
