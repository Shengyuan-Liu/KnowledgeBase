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
for quote in ['does not have the same behavior for /messages and Files API endpoints', 'it is ignored for /messages', 'is required (with value files-api-2025-04-14) for Files API endpoints']:
    claim(x,quote,quote,h)
claim(x,'The anthropic-version header is ignored', 'Version status is ignored without added endpoint scope.',[(2,'| anthropic-version | Ignored |')])
reviews[x]['findings'].append('Both endpoint behaviors and exact version status are supported and locally cited; the earlier uncited opening/bullet is absent.')
x='accept-independent-passfail'
claim(x,'up to 6 credits of independent study (DS-GA 1010) to the MSDS degree','Independent-study limit.',[(1,'MSDS students can apply up to 6 credits of independent study')])
pf=[(1,'Only 1 elective (this does not include')]
for quote in ['Only 1 elective', 'this does not include the “One Data Science Elective” requirement', 'DS-GA 1009 can be taken as pass/fail and count towards the MSDS degree', 'Students in the Industry Concentration can use their 1 elective allowance for an Industry Concentration elective']:
    claim(x,quote,quote,pf)
# The required-course prohibition occurs twice; retain both claim occurrences.
for occurrence in range(2):
    claim(x,'Required courses for the degree cannot be taken as pass/fail',f'Required-course prohibition, occurrence {occurrence+1}.',pf)
reviews[x]['findings'].append('All requested restrictions preserved. One prohibition is unnecessarily repeated; a style-instruction miss, not a new unsupported fact.')
x='accept-awards-jobs'
sch=[(i,'CDS offers a limited number of tuition scholarships') for i in [1,2]]
for quote in ['All applicants for admission are considered for tuition scholarships', 'on a competitive basis', 'Scholarship recipients will be notified in their admit letter']:
    claim(x,quote,quote,sch)
claim(x,'there is no separate scholarship application process','No separate application.',[(1,'There is no separate scholarship application process.')],
      reason='Supported by the admissions FAQ only. Assign the paragraph citations by clause: [1] to this clause, [1][2] to shared facts. Do not invent a wrong citation-pair judgment solely from a multi-claim paragraph. The requested general FAQ lacks this statement and the response does not identify the other FAQ in prose; source-scope compliance separately fails.')
jobs=[(i,'On-campus positions are available at CDS and NYU') for i in [1,2]]
for quote in ['On-campus research or teaching assistant positions are not guaranteed','such positions are available','competitive, and are typically posted on a semester-by-semester basis']:
    claim(x,quote,quote,jobs)
reviews[x]['named_source_compliance']=False
reviews[x]['findings'].append('All requested v2 facts are answered and the extra application-process fact has source support in [1]. However, an answer requested from the general FAQ blends in admissions-only information without explicitly naming that other document. This violates the frozen source-specific instruction; do not label the fact itself fabricated or the citation IDs invalid.')
reviews[x]['findings'].append('Under the original rubric the first point is partial because limited scholarship count is absent. Job competition and posting cadence are present. Under v2 the limited count is optional, not a completeness defect.')
x='accept-unspecified-api-error'
claim(x,'the content type "search_result" is "Not Supported"','search_result status.',[(1,r'| content | array, type = "search\_result" |  | Not Supported |')])
reviews[x]['findings'].append('Both exact error details are explicitly unavailable; no HTTP status or JSON body invented. Repeated absence statement is not counted as a positive factual claim.')
x='accept-personal-study-approval'
reviews[x]['findings'].append('Both individual approval and supervisor assignment are explicitly unavailable. No personal outcome, contact or procedural advice is invented. The citations accompany absence statements and are valid IDs, not positive source facts; claim-free abstention is exempt from factual citation coverage.')

if __name__=='__main__':
    assert not (DIR/'manual-review.json').exists()
    originals={c['id']:c for c in json.loads((DIR/'original-cases.json').read_text())}
    for identity,r in reviews.items():
        r['language_compliance']=True
        r.setdefault('named_source_compliance', True)
        r['points']=[{'reference':p,'correctness':score,'present':True} for p,score in zip(cases[identity]['expected_answer_points'],r.pop('point_scores'),strict=True)]
        old_scores=[2]*len(r['points'])
        if identity=='accept-awards-jobs':old_scores[0]=1
        r['original_rubric_points']=[{'reference':p,'correctness':score,'present':True} for p,score in zip(originals[identity]['expected_answer_points'],old_scores,strict=True)]
        r['pass']=all(p['correctness']==2 for p in r['points']) and all(c['verdict']=='supported' for c in r['claims']) and all(c['citation_verdict']=='supported' for c in r['claims'] if c['associated_citations']) and (cases[identity]['answerable'] or r['appropriate_abstention']) and r['named_source_compliance'] and r['language_compliance']
    write_json(DIR/'manual-review.json',list(reviews.values()))
