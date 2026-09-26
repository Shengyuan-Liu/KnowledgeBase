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
claim(x,'Full-time CDS students register for 9 credits per semester.','Full-time CDS students register for nine credits per semester.',[(1,'Full-time CDS students register for 9 credits.')])
claim(x,'Part-time students register for less than 9 credits per semester','Part-time CDS students register for fewer than nine credits per semester.',[(1,'Part-time students register for less than 9 credits.')])
claim(x,'Students should plan on spending 10–15 hours per week per data science course, assuming they have all the prerequisites.','The workload estimate is 10–15 hours per course per week, conditional on prerequisites.',[(1,'Students should plan on spending 10-15 hours per week')])
for quote,statement in [('The courses are graduate-level','Courses are graduate-level.'),('move very quickly','Courses move quickly.'),('making it difficult to catch up if you fall behind','Falling behind makes catching up difficult.')]:
    claim(x,quote,statement,[(1,'The data science courses are graduate-level courses')])
x='accept-independent-passfail'
claim(x,'MSDS students can apply up to 6 credits of independent study (DS-GA 1010) to the MSDS degree','At most six DS-GA 1010 credits count toward the degree.',[(1,'MSDS students can apply up to 6 credits of independent study')])
pf=[(1,'Only 1 elective (this does not include'),(3,'MSDS students can only take 1 elective')]
for quote,statement in [
('Only 1 elective','Only one elective can count pass/fail.'),
('(not including the required “One Data Science Elective”)','The designated Data Science Elective is excluded.'),
('and DS-GA 1009 can be taken as pass/fail and count towards the MSDS degree.','DS-GA 1009 can count pass/fail.'),
('Required courses for the degree cannot be taken as pass/fail','Required degree courses cannot count pass/fail.'),
('The allowance to take one elective pass/fail specifically excludes the “One Data Science Elective” requirement','The exclusion is repeated.'),
('required core courses','Required core courses cannot count pass/fail, in the stated degree-credit context.'),
('the designated Data Science Elective must not be taken pass/fail','The designated elective cannot count pass/fail, in the stated degree-credit context.')]:
    claim(x,quote,statement,pf)
claim(x,'Students in the Industry Concentration can use their 1 elective pass/fail allowance for an Industry Concentration elective','The Industry Concentration can use its one-elective allowance for a concentration elective.',[(1,'Students in the Industry Concentration can use their 1 elective allowance')])
x='accept-course-two-areas'
needle=cases[x]['evidence'][0]['quote']
for quote,statement in [
('DS-GA 1012, titled "Large Language Models: Evaluation and Applications,"','The course code and current title match.'),
('is listed under both the Big Data and Natural Language Processing subject areas','The course occurs in both subject lists.'),
('This course was formerly known as "Natural Language Understanding and Computational Semantics"','The former title matches the parenthetical source note.')]:
    claim(x,quote,statement,[(2,needle)])
x='accept-awards-jobs'
scholar=[(1,'CDS offers a limited number of tuition scholarships'),(2,'CDS offers a limited number of tuition scholarships')]
for quote,statement in [('All applicants for admission are considered','All admission applicants are considered.'),("CDS's limited number of tuition scholarships",'The number of scholarships is limited.'),('on a competitive basis','Scholarship awards are competitive.')]:claim(x,quote,statement,scholar)
claim(x,'there is no separate scholarship application process','No separate scholarship application is required, as stated in the supplied admissions FAQ.',[(1,'There is no separate scholarship application process.')],citations=[1])
reviews[x]['findings'].append('The extra no-separate-application statement is supported by admissions FAQ source 1. Source 2 supports the preceding eligibility/competition clause, not that added fact. It is not an invented inference from automatic consideration.')
claim(x,'Scholarship recipients will be notified in their admit letter','Recipients are notified in their admit letter.',scholar)
jobs=[(1,'On-campus positions are available at CDS and NYU'),(2,'On-campus positions are available at CDS and NYU')]
for quote,statement in [('On-campus research and teaching assistant positions are available at CDS and NYU','Such positions are available at CDS and NYU.'),('such opportunities are not guaranteed for any given student','No individual is guaranteed a position.'),('These positions are competitive','Positions are competitive.'),('are typically posted on a semester-by-semester basis','Positions are typically posted each semester.')]:claim(x,quote,statement,jobs)
x='accept-beta-header-scope'
header=[(2,'| anthropic-beta | Ignored for `/messages`;')]
claim(x,'No, anthropic-beta does not have the same behavior for /messages and Files API endpoints in the DeepSeek Anthropic-compatible API.','The header behavior differs by endpoint family.',header,citations=[])
claim(x,'For /messages endpoints, the anthropic-beta HTTP header is ignored','anthropic-beta is ignored for /messages.',header)
claim(x,'For Files API endpoints, the anthropic-beta header is required and must be set to files-api-2025-04-14','Files endpoints require the stated beta header value.',header)
claim(x,'For anthropic-version, it is always ignored (not used) on all endpoints','anthropic-version is ignored always on all endpoints.',[(2,'| anthropic-version | Ignored |')],verdict='insufficient',
    reason='The table establishes Ignored in the guide compatibility scope. It does not enumerate or establish a universal all-endpoint guarantee. The extra universal qualifier is unsupported, not proven false by this source. The requested core status is correct, but the stronger full claim is not established.')
reviews[x]['point_scores'][1]=1
reviews[x]['findings'].append('Scope overstatement: remove always/on all endpoints when stating the table entry. This fails the frozen requirement to preserve scope and fully support each associated citation. It is an assessment of source support, not an external claim about actual API behavior.')
x='accept-message-subfields'
for quote,statement,needle in [
('The text content citations field (content → array, type="text" → citations) is Ignored','Text content citations are ignored.',r'| content | array, type="text" | citations | Ignored |'),
('The tool_use id field (content → array, type="tool_use" → id) is Fully Supported','tool_use.id is fully supported.',r'| content | array, type = "tool\_use" | id | Fully Supported |'),
('The tool_result is_error field (content → array, type="tool_result" → is_error) is Ignored','tool_result.is_error is ignored.',r'| content | array, type = "tool\_result" | is\_error | Ignored |')]:claim(x,quote,statement,[(1,needle)])
x='accept-unspecified-api-error'
needle=r'| content | array, type = "search\_result" |  | Not Supported |'
claim(x,'The saved DeepSeek Anthropic guide promises that when a request contains a content block of type search_result (i.e., content as array, type = "search_result"), this is Not Supported.','search_result content is marked Not Supported.',[(1,needle)])
claim(x,'The relevant table states only the support status as "Not Supported" for search_result content blocks','The table reports Not Supported for this content type.',[(1,needle)])
reviews[x]['findings'].append('All supplied excerpts were inspected: no exact HTTP error code/body is given. The answer abstains from inventing either. Missing-information acknowledgments are reviewed as abstention, not fabricated factual claims.')
x='accept-personal-study-approval'
claim(x,'The sources only address general policies','The supplied sources discuss general degree policies.',[(1,'MSDS students can apply up to 6 credits of independent study'),(2,'The curriculum for the MS in Data Science (MSDS) degree is 36 credits.')])
claim(x,'such as the number of independent study credits you may apply to the MSDS degree','The sources discuss how many independent-study credits count.',[(1,'MSDS students can apply up to 6 credits of independent study')],citations=[1])
reviews[x]['findings'].append('The personal decision and supervisor remain unknown. The answer invents neither a person nor an approved/rejected status nor a contact. Citation 1 supports the independent-study cap; citation 2 supports the preceding general-curriculum clause. Missing-information statements are assessed under abstention.')

if __name__=='__main__':
    assert not (DIR/'manual-review.json').exists()
    for identity,r in reviews.items():
        r['points']=[{'reference':p,'correctness':score,'present':True} for p,score in zip(cases[identity]['expected_answer_points'],r.pop('point_scores'),strict=True)]
        r['pass']=all(p['correctness']==2 for p in r['points']) and all(c['verdict']=='supported' for c in r['claims'])
        r['citation_association_note']='Citation IDs in the same prose paragraph can support distinct clauses; each record names only the semantically associated IDs. References to absence of information are assessed in abstention.'
    write_json(DIR/'manual-review.json',list(reviews.values()))
    print('Manual review recorded for all 8 answers:',sum(len(r['claims']) for r in reviews.values()),'claim occurrences; one unsupported universal qualifier.')
