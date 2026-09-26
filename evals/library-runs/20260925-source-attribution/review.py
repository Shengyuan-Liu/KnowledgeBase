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
claim(x,'No, anthropic-beta does not have the same behavior for /messages and Files API endpoints:','Beta behavior differs between endpoint families.',h,citations=[])
claim(x,'The anthropic-beta header is ignored','Beta is ignored for /messages.',h)
claim(x,'The anthropic-beta header is required and must be set to files-api-2025-04-14','Files endpoints require this beta value.',h)
claim(x,'It is ignored for all endpoints','Version header is ignored for all endpoints.',[(2,'| anthropic-version | Ignored |')],verdict='insufficient',reason='Ignored does not explicitly establish the added all-endpoint guarantee; same conservative scope criterion as baseline.')
reviews[x]['point_scores'][1]=1
reviews[x]['findings'].append('Universal endpoint qualification remains despite the new exact-status instruction. The status itself is correct; its added scope is not established.')
x='accept-independent-passfail'
cap=[(1,'MSDS students can apply up to 6 credits of independent study')]
pf=[(1,'Only 1 elective (this does not include')]
claim(x,'MSDS students can apply up to 6 credits of independent study (DS-GA 1010) to the MSDS degree','At most six credits count.',cap)
for quote,statement in [('Only 1 elective','Only one elective can count pass/fail.'),('this does not include the “One Data Science Elective” requirement','Designated elective is excluded.'),('and DS-GA 1009 can be taken as pass/fail and count towards the MSDS degree','DS-GA 1009 can count pass/fail.'),('Students in the Industry Concentration can use their 1 elective allowance for an Industry Concentration elective','The concentration can use the one-elective allowance within its elective list.'),('Required courses for the degree cannot be taken as pass/fail','Required courses cannot count pass/fail.'),('Industry Concentration students may choose an Industry Concentration elective as their one pass/fail elective','The concentration allowance is repeated.')]:claim(x,quote,statement,pf)
for quote,statement in [('The allowance is for “only 1 elective” and DS-GA 1009','The allowance is repeated.'),('required core courses (including the required Data Science Elective) must be taken for a letter grade','Required core/designated elective are excluded from the pass/fail allowance.')]:claim(x,quote,statement,pf,citations=[])
reviews[x]['findings'].append('Required restrictions preserved. The first summary bullet is uncited; the next bullet citation does not cover it. This lowers citation coverage but is not an unsupported fact.')
x='accept-awards-jobs'
sch=[(2,'CDS offers a limited number of tuition scholarships')]
for quote,statement in [('All applicants for admission are considered for tuition scholarships','All admission applicants are considered.'),('on a competitive basis','Awards are competitive.'),('all applicants are automatically considered as part of the admissions process','All admission applicants are considered, repeated.'),('Scholarship recipients will be notified in their admit letter','Notification is in the admit letter.')]:claim(x,quote,statement,sch)
claim(x,'There is no separate scholarship application process','No separate scholarship application.',[(1,'There is no separate scholarship application process.')],citations=[2],reason='Supported in admissions FAQ source 1, not the cited general FAQ source 2.')
reviews[x]['claims'][-1]['citation_verdict']='insufficient'
jobs=[(2,'On-campus positions are available at CDS and NYU')]
for quote,statement in [('On-campus positions are available at the Center for Data Science (CDS) and NYU','Positions are available.'),('such opportunities are not guaranteed for any given student','Positions are not individually guaranteed.'),('These positions are competitive','Positions are competitive.'),('typically posted on a semester-by-semester basis','Typically advertised each semester.')]:claim(x,quote,statement,jobs)
claim(x,'All the above points are directly supported by the general FAQ','All preceding statements are in the general FAQ.',[(2,'CDS offers a limited number of tuition scholarships'),(1,'There is no separate scholarship application process.')],citations=[2],verdict='insufficient',reason='The separate-application statement is not in the general FAQ. This explicit attribution is unsupported.')
reviews[x]['point_scores'][0]=1
reviews[x]['findings'].append('Wrong-FAQ citation and blanket source attribution remain. Limited number of scholarships is also omitted from the required first reference point; other required facts are present.')
x='accept-unspecified-api-error'
needle=r'| content | array, type = "search\_result" |  | Not Supported |'
claim(x,'it is "Not Supported"','search_result is Not Supported.',[(1,needle)])
claim(x,'The available documentation only identifies lack of support for this content type','Lack of support is identified.',[(1,needle)],citations=[])
reviews[x]['findings'].append('All excerpts inspected; exact HTTP status/body correctly withheld. Repeated support-status sentence is uncited in its own paragraph under the unchanged local association rule.')
x='accept-personal-study-approval'
claim(x,'MSDS students can apply up to 6 credits of independent study (DS-GA 1010) toward the degree','Up to six credits count.',[(1,'MSDS students can apply up to 6 credits of independent study')])
claim(x,'lists DS-GA 1010 as an available elective','DS-GA 1010 is an elective option.',[(2,'DS-GA 1010 Independent Study')])
claim(x,'describes general requirements and curricula','Source 2 describes the general curriculum.',[(2,'The curriculum for the MS in Data Science (MSDS) degree is 36 credits.')])
reviews[x]['findings'].append('All supplied excerpts inspected. No personal approval/supervisor or contact invented; absence statements assessed under abstention. Leading Source [n] inside the same list item counts as an associated citation under the original protocol.')

if __name__=='__main__':
    assert not (DIR/'manual-review.json').exists()
    for identity,r in reviews.items():
        r['points']=[{'reference':p,'correctness':score,'present':True} for p,score in zip(cases[identity]['expected_answer_points'],r.pop('point_scores'),strict=True)]
        r['pass']=all(p['correctness']==2 for p in r['points']) and all(c['verdict']=='supported' for c in r['claims']) and all(c['citation_verdict']=='supported' for c in r['claims'] if c['associated_citations'])
    write_json(DIR/'manual-review.json',list(reviews.values()))
