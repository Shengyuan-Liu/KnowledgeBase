"""Record Codex's explicit claim review; do not edit generated answers or criteria."""
import json
from pathlib import Path
from evals.evaluate import digest,read_jsonl,write_json
DIR=Path(__file__).parent
answers={a['case_id']:a for a in read_jsonl(DIR/'answers.jsonl')}
cases={c['id']:c for c in json.loads((DIR/'cases.json').read_text())}
reviews={identity:{'case_id':identity,'reviewer':'Codex','answer_sha256':digest(a['answer'].encode()),'claims':[],
    'point_scores':[2]*len(cases[identity]['expected_answer_points']),'relevance':2,'abstains':not cases[identity]['answerable'],
    'appropriate_abstention':not cases[identity]['answerable'],'incorrect_abstention':False,'findings':[]}
    for identity,a in answers.items()}


def source_evidence(identity,source_id,needle):
    source=next(s for s in answers[identity]['sources'] if s['source_id']==source_id)
    start=source['text'].index(needle)
    left=source['text'].rfind('\n\n',0,start)+2
    if left==1:left=0
    right=source['text'].find('\n\n',start+len(needle))
    if right<0:right=len(source['text'])
    return {'source_id':source_id,'file_name':source['file_name'],
        'start_offset':source['start_offset']+left,'end_offset':source['start_offset']+right,
        'quote':source['text'][left:right]}


def claim(identity,answer_quote,statement,support,*,citations=None,verdict='supported',reason=None):
    assert answer_quote in answers[identity]['answer']
    evidence=[source_evidence(identity,*entry) for entry in support]
    rows=reviews[identity]['claims']
    rows.append({'id':f'c{len(rows)+1}','answer_quote':answer_quote,'statement':statement,
        'verdict':verdict,'evidence':evidence,'associated_citations':list(dict.fromkeys(e['source_id'] for e in evidence)) if citations is None else citations,
        'citation_verdict':verdict if (citations is None or citations) else 'missing',
        'reason':reason or 'The exact supplied source text supports this claim, including its qualification.'})


x='accept-beta-header-scope'
h=[(2,'| anthropic-beta | Ignored for `/messages`;')]
for quote,statement in [('No. `anthropic-beta` does **not** have the same behavior','Beta behavior differs.'),('**ignored for `/messages`**','Beta ignored for messages.'),('**required (`files-api-2025-04-14`) for Files API endpoints**','Files require the specified beta value.')]:claim(x,quote,statement,h)
claim(x,'`anthropic-version` is **ignored**','Version ignored.',[(2,'| anthropic-version | Ignored |')])
reviews[x]['findings'].append('The contradictory Yes and unsupported all-endpoint version scope are absent. All three header facts and the contrast are supported.')
x='accept-independent-passfail'
pf=[(1,'Only 1 elective (this does not include')]
claim(x,'**up to 6 credits** of **DS-GA 1010 Independent Study** can be applied to the MSDS degree','Up to six independent-study credits count.',[(1,'MSDS students can apply up to 6 credits of independent study')])
for quote,statement in [('**only 1 elective**','One-elective allowance.'),('**not including the “One Data Science Elective” requirement**','Designated elective excluded.'),('**DS-GA 1009** can be taken pass/fail and count toward the MSDS degree','DS-GA 1009 allowed.'),('**Required courses cannot be taken pass/fail**','Required courses excluded.'),('**students in the Industry Concentration can use their 1-elective pass/fail allowance for an Industry Concentration elective**','Concentration allowance preserved.')]:claim(x,quote,statement,pf)
x='accept-awards-jobs'
sch=[(2,'CDS offers a limited number of tuition scholarships')]
for quote,statement in [('all applicants for admission are considered for tuition scholarships','All applicants considered.'),('on a competitive basis','Awards competitive.'),('Scholarship recipients are notified in their admit letter','Admit-letter notification.')]:claim(x,quote,statement,sch)
claim(x,'there is no separate scholarship application process','No separate scholarship application.',[(1,'There is no separate scholarship application process.')],citations=[2],reason='The extra fact is in admissions FAQ source 1; cited general FAQ source 2 does not state it.')
reviews[x]['claims'][-1]['citation_verdict']='insufficient'
jobs=[(2,'On-campus positions are available at CDS and NYU')]
for quote,statement in [('positions are available at CDS and NYU','Positions available.'),('they are not guaranteed for any given student','No individual guarantee.'),('**competitive**','Positions competitive.'),('**typically posted on a semester-by-semester basis**','Typically advertised each semester.')]:claim(x,quote,statement,jobs)
reviews[x]['point_scores'][0]=1
reviews[x]['findings'].append('Only remaining failing case: wrong-FAQ support for the extra application-process statement and omission of the limited number of awards.')
x='accept-unspecified-api-error'
claim(x,'**Not Supported** in DeepSeek’s Anthropic API compatibility table','search_result Not Supported.',[(1,r'| content | array, type = "search\_result" |  | Not Supported |')])
reviews[x]['findings'].append('All excerpts inspected; exact status/body appropriately withheld.')
x='accept-personal-study-approval'
claim(x,'DS-GA 1010 Independent Study is an elective option','Independent study elective option.',[(2,'DS-GA 1010 Independent Study')])
claim(x,'MSDS students can apply up to 6 credits of independent study toward the degree','Up to six credits count.',[(1,'MSDS students can apply up to 6 credits of independent study')])
reviews[x]['findings'].append('Both personal facts explicitly unknown, no contact advice. Shared paragraph [2][1] assigned to the two supported clauses respectively.')

if __name__=='__main__':
    assert not (DIR/'manual-review.json').exists()
    for identity,r in reviews.items():
        r['points']=[{'reference':p,'correctness':score,'present':True} for p,score in zip(cases[identity]['expected_answer_points'],r.pop('point_scores'),strict=True)]
        r['pass']=all(p['correctness']==2 for p in r['points']) and all(c['verdict']=='supported' for c in r['claims']) and all(c['citation_verdict']=='supported' for c in r['claims'] if c['associated_citations']) and (cases[identity]['answerable'] or r['appropriate_abstention'])
    write_json(DIR/'manual-review.json',list(reviews.values()))
