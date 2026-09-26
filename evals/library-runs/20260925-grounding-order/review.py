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
claim(x,'No. In the DeepSeek Anthropic guide:','Beta behavior differs between the two endpoint families.',h,citations=[])
claim(x,'For the /messages endpoint, the anthropic-beta header is "Ignored".','Beta is ignored for /messages.',h,citations=[])
claim(x,'For the Files API endpoints, the anthropic-beta header is "required" (and must be set to files-api-2025-04-14)','Files endpoints require the stated beta value.',h)
claim(x,'The anthropic-version header is "Ignored"','Version header status is Ignored.',[(2,'| anthropic-version | Ignored |')])
reviews[x]['findings'].append('Observed universal-scope defect disappears: version status is quoted without an added endpoint guarantee. The introductory No and first beta bullet are uncited; the second bullet citation does not cover them.')
x='accept-independent-passfail'
pf=[(1,'Only 1 elective (this does not include')]
claim(x,'MSDS students can apply up to 6 credits of independent study (DS-GA 1010) to the MSDS degree','Up to six independent-study credits count.',[(1,'MSDS students can apply up to 6 credits of independent study')])
for quote,statement in [('Only 1 elective','Only one elective can count pass/fail.'),('this does not include the “One Data Science Elective” requirement','Designated elective excluded.'),('and DS-GA 1009 can be taken as pass/fail and count towards the MSDS degree','DS-GA 1009 can count pass/fail.'),('Required courses for the degree cannot be taken as pass/fail','Required courses excluded.'),('The “One Data Science Elective” requirement is excluded from the pass/fail option allowance.','Designated-elective exclusion repeated.'),('you cannot use the pass/fail option for the core-required "One Data Science Elective"','Same required-elective exclusion restated.'),('Students in the Industry Concentration can use their 1 elective allowance for an Industry Concentration elective','Industry concentration allowance preserved.'),('that Industry Concentration elective may be taken pass/fail and count towards the degree','Concentration allowance paraphrased.')]:claim(x,quote,statement,pf)
reviews[x]['findings'].append('All required points/restrictions remain correct. Repeated explanatory clauses counted separately; filename reference is source metadata, not a new substantive claim.')
x='accept-awards-jobs'
sch=[(2,'CDS offers a limited number of tuition scholarships')]
for quote,statement in [('All applicants for admission are considered for tuition scholarships','All admission applicants considered.'),('on a competitive basis','Awards competitive.'),('consideration is automatic when you apply for admission','All admission applicants considered, restated.'),('Scholarship recipients are notified in their admit letter','Notification in admit letter.')]:claim(x,quote,statement,sch)
claim(x,'There is no separate scholarship application process','No separate scholarship application.',[(1,'There is no separate scholarship application process.')],citations=[2],reason='Supported in source 1, not cited source 2.')
reviews[x]['claims'][-1]['citation_verdict']='insufficient'
jobs=[(2,'On-campus positions are available at CDS and NYU')]
for quote,statement in [('On-campus positions (including research and teaching assistant positions) are available at CDS and NYU','Positions available.'),('such opportunities are not guaranteed for any student','No individual guarantee.'),('These positions are competitive','Positions competitive.'),('are typically posted on a semester-by-semester basis','Typically advertised each semester.')]:claim(x,quote,statement,jobs)
reviews[x]['point_scores'][0]=1
reviews[x]['findings'].append('Wrong-FAQ attribution remains. Limited scholarship count is omitted from the required first reference point.')
x='accept-unspecified-api-error'
needle=r'| content | array, type = "search\_result" |  | Not Supported |'
claim(x,'is "Not Supported" [1]','search_result marked Not Supported.',[(1,needle)])
claim(x,'The guide states that content blocks of type search_result are "Not Supported"','Support status repeated.',[(1,needle)])
reviews[x]['findings'].append('Exact HTTP status/body withheld. Parenthetical 400/422 are explicitly examples of information not given, not claimed error responses.')
x='accept-personal-study-approval'
claim(x,'for academic-related questions, the general contact listed is cds-masters@nyu.edu','This address is a general academic-question contact.',[(2,'If you have any questions regarding the eligibility of a course to serve as a general elective, please contact cds-masters@nyu.edu.')],citations=[1,2],verdict='insufficient',reason='Source 2 gives this address specifically for general-elective course eligibility, not all academic questions or personal independent-study approval. Source 1 does not contain the address. The answer adds inapplicable contact advice despite correctly acknowledging missing personal information.')
reviews[x]['appropriate_abstention']=False
reviews[x]['findings'].append('Personal approval/supervisor are withheld, but a next-step contact is added without support for this requested issue. The frozen appropriate-abstention/no-unsupported-advice criterion fails; this is partial abstention, not invented approval.')

if __name__=='__main__':
    assert not (DIR/'manual-review.json').exists()
    for identity,r in reviews.items():
        r['points']=[{'reference':p,'correctness':score,'present':True} for p,score in zip(cases[identity]['expected_answer_points'],r.pop('point_scores'),strict=True)]
        r['pass']=all(p['correctness']==2 for p in r['points']) and all(c['verdict']=='supported' for c in r['claims']) and all(c['citation_verdict']=='supported' for c in r['claims'] if c['associated_citations']) and (cases[identity]['answerable'] or r['appropriate_abstention'])
    write_json(DIR/'manual-review.json',list(reviews.values()))
