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


x='accept-load-hours'
for quote,needle in [('full-time students register for 9 credits','Full-time CDS students register for 9 credits.'),('part-time students register for less than 9 credits','Part-time students register for less than 9 credits.'),('A student with the prerequisites should plan to spend 10–15 hours per week on each data science course','Students should plan on spending 10-15 hours per week')]:
    claim(x,quote,quote,[(1,needle)])
x='accept-independent-passfail'
claim(x,'The maximum number of independent study (DS-GA 1010) credits that can count toward the MSDS degree is 6 credits','Six-credit maximum.',[(1,'MSDS students can apply up to 6 credits of independent study')])
for quote in ['Only 1 elective','this does not include the “One Data Science Elective” requirement','DS-GA 1009 can be taken as pass/fail and count towards the MSDS degree','Students in the Industry Concentration can use their 1 elective pass/fail allowance for an Industry Concentration elective','Required courses for the degree cannot be taken as pass/fail']:
    claim(x,quote,quote,[(1,'Only 1 elective (this does not include')])
x='accept-course-two-areas'
for quote in ['DS-GA 1012 is listed under both Big Data and Natural Language Processing (NLP) subject areas','The current course title given is Large Language Models: Evaluation and Applications','formerly Natural Language Understanding and Computational Semantics']:
    claim(x,quote,quote,[(1,cases[x]['evidence'][0]['quote'])])
x='accept-awards-jobs'
for quote in ['Applicants are considered for tuition scholarships on a competitive basis','all applicants for admission are considered for these awards','Scholarship recipients are notified in their admit letter']:
    claim(x,quote,quote,[(1,'CDS offers a limited number of tuition scholarships')])
for quote in ['An on-campus research or teaching position is not guaranteed','on-campus positions are available','are competitive and not guaranteed for any given student']:
    claim(x,quote,quote,[(1,'On-campus positions are available at CDS and NYU')])
reviews[x]['findings'].append('The original source-mixing defect is absent: only general-FAQ evidence is supplied, with no separate-application assertion. Requested v2 points are complete; optional limited-count and posting-cadence details from the original rubric are omitted.')
x='accept-beta-header-scope'
for quote in ['the anthropic-beta header does not have the same behavior for /messages and Files API endpoints','ignored for /messages','required (files-api-2025-04-14) for Files API endpoints']:
    claim(x,quote,quote,[(2,'| anthropic-beta | Ignored for `/messages`;')])
claim(x,'The anthropic-version header is "ignored"','Literal version status.',[(2,'| anthropic-version | Ignored |')])
x='accept-message-subfields'
for quote,needle in [('For text content citations (content | array, type="text" | citations), the support status is "Ignored"',r'| content | array, type="text" | citations | Ignored |'),('For tool_use id (content | array, type = "tool_use" | id), the support status is "Fully Supported"',r'| content | array, type = "tool\_use" | id | Fully Supported |'),('For tool_result is_error (content | array, type = "tool_result" | is_error), the support status is "Ignored"',r'| content | array, type = "tool\_result" | is\_error | Ignored |')]:
    claim(x,quote,quote,[(1,needle)])
x='accept-unspecified-api-error'
claim(x,'a search_result content block is "Not Supported"','Recorded support status.',[(1,r'| content | array, type = "search\_result" |  | Not Supported |')])
reviews[x]['findings'].append('Exact HTTP error code and JSON payload are both explicitly unavailable; neither is invented.')
x='accept-personal-study-approval'
reviews[x]['findings'].append('Claim-free abstention on both personal facts; valid citations accompany evidence-absence statements, not positive factual claims. No contact advice invented.')
x='scope-compare-faqs'
claim(x,'the page explicitly stating there is no separate scholarship application process is the general FAQ page','The statement is attributed to the general FAQ.',[(1,'There is no separate scholarship application process.')],verdict='unsupported',reason='Source [1] is the admissions FAQ, not the general FAQ. All three supplied sources come from admissions. The scope resolves both files, but top-K selects only admissions chunks; the general-FAQ gold span is absent. This sentence misnames its actual source.')
claim(x,'All applicants for admission are considered for these awards on a competitive basis. There is no separate scholarship application process. Scholarship recipients will be notified in their admit letter','Quoted financial paragraph exists in admissions FAQ.',[(1,'There is no separate scholarship application process.')])
reviews[x]['point_scores']=[0,0]
reviews[x]['findings'].append('FAIL: 50% gold evidence coverage. Restricting eligible files to both requested documents does not ensure both survive global top-K. Generation then misidentifies the only supplied FAQ. Preserve this before any ranking/identity correction.')
for x in ['scope-ambiguous-faq','scope-missing-file']:
    reviews[x]['findings'].append('Correct deterministic clarification; no embedding/generation call and no evidence. Scope status/candidates are preserved in events and the completed snapshot.')

if __name__=='__main__':
    assert not (DIR/'manual-review.json').exists()
    originals={c['id']:c for c in json.loads((DIR/'original-cases.json').read_text())}
    for identity,r in reviews.items():
        r['language_compliance']=True
        r['named_source_compliance']=identity!='scope-compare-faqs'
        r['points']=[{'reference':p,'correctness':score,'present':score>0} for p,score in zip(cases[identity]['expected_answer_points'],r.pop('point_scores'),strict=True)]
        if identity in originals:
            scores=[2]*len(r['points'])
            if identity=='accept-awards-jobs':scores=[1,2,1]
            r['original_rubric_points']=[{'reference':p,'correctness':v,'present':True} for p,v in zip(originals[identity]['expected_answer_points'],scores,strict=True)]
        r['pass']=all(p['correctness']==2 for p in r['points']) and all(c['verdict']=='supported' for c in r['claims']) and all(c['citation_verdict']=='supported' for c in r['claims'] if c['associated_citations']) and r['named_source_compliance']
    write_json(DIR/'manual-review.json',list(reviews.values()))
