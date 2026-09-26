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
header=[(2,'| anthropic-beta | Ignored for `/messages`;')]
claim(x,'No, anthropic-beta does not have the same behavior for /messages and Files API endpoints.','The two endpoint families have different beta-header behavior.',header)
claim(x,'For /messages, the anthropic-beta header is ignored.','The beta header is ignored for /messages.',header)
claim(x,'For Files API endpoints, the anthropic-beta header is required and must be set to files-api-2025-04-14','Files endpoints require the stated beta value.',header)
claim(x,'The anthropic-version header is ignored in both cases','The version header is ignored in both endpoint families.',[(2,'| anthropic-version | Ignored |')],verdict='insufficient',
      reason='Conservative scope assessment: the row says Ignored without endpoint-specific version-header guarantees. Both cases is a narrower claim than all endpoints but still adds endpoint scope. This interpretation is debatable and is not proof of contrary real API behavior; the replay does not clearly resolve the original scope concern.')
reviews[x]['point_scores'][1]=1
reviews[x]['findings'].append('The original always/all-endpoints wording disappeared, but both cases remains an explicit scope inference. Conservatively leave the observed issue unresolved. Even accepting this interpretation would not make this run pass because the awards answer independently fails citation/source identity.')

x='accept-independent-passfail'
cap=[(1,'MSDS students can apply up to 6 credits of independent study')]
pf=[(1,'Only 1 elective (this does not include'),(3,'MSDS students can only take 1 elective')]
industry=[(1,'Students in the Industry Concentration can use their 1 elective allowance')]
for quote in ['MSDS students can apply up to 6 credits of independent study (DS-GA 1010) to the MSDS degree','Up to 6 credits of DS-GA 1010 Independent Study can count toward the MSDS degree']:
    claim(x,quote,'At most six DS-GA 1010 credits count.',cap)
for quote,statement in [
('Only 1 elective (not including','Only one elective can count pass/fail.'),
('not including the “One Data Science Elective” requirement','The designated elective is excluded.'),
('and DS-GA 1009 can be taken as pass/fail and counted towards the MSDS degree','DS-GA 1009 can count pass/fail.'),
('Only 1 elective (excluding','The one-elective restriction is repeated.'),
('excluding the Data Science Elective requirement','The designated-elective exclusion is repeated.'),
('and DS-GA 1009 can be counted as pass/fail','The DS-GA 1009 allowance is repeated.'),
('Required courses cannot be taken pass/fail','Required degree courses cannot count pass/fail, in the stated degree-credit context.')]:claim(x,quote,statement,pf)
claim(x,'Required courses for the degree cannot be taken as pass/fail.','Required degree courses cannot count pass/fail.',[(1,'Required courses for the degree cannot be taken as pass/fail.')])
for quote in ['For students in the Industry Concentration, the single elective pass/fail allowance may be used for an Industry Concentration elective',
              'The 1 elective pass/fail allowance may be used for an Industry Concentration elective']:
    claim(x,quote,'The concentration can use its one-elective allowance within the concentration.',industry)
reviews[x]['findings'].append('Explicit only, maximum credits, exclusion, required-course rule and Industry Concentration allowance are all retained. The redundant summary repeats supported facts; each occurrence is inventoried.')

x='accept-awards-jobs'
scholar=[(2,'CDS offers a limited number of tuition scholarships')]
for quote,statement in [('All applicants for admission are considered','All admission applicants are considered.'),('the limited number of tuition scholarships offered by CDS','Scholarships are limited.'),('on a competitive basis','Awards are competitive.')]:claim(x,quote,statement,scholar)
claim(x,'There is no separate application process for these scholarships','No separate scholarship application process.',[(1,'There is no separate scholarship application process.')],citations=[2],
      reason='The statement exists in supplied admissions FAQ source 1, but the answer cites general FAQ source 2, where it is absent. Supported in context, unsupported by its actual associated citation.')
reviews[x]['claims'][-1]['citation_verdict']='insufficient'
claim(x,'Scholarship recipients are notified in their admit letter','Recipients are notified in the admit letter.',scholar)
jobs=[(2,'On-campus positions are available at CDS and NYU')]
for quote,statement in [('On-campus positions (including research and teaching assistant roles) are available at CDS and NYU','Such positions are available at CDS and NYU.'),('such opportunities are not guaranteed for any given student','Positions are not individually guaranteed.'),('These positions are competitive','Positions are competitive.'),('are typically posted on a semester-by-semester basis','Positions are typically advertised each semester.')]:claim(x,quote,statement,jobs)
claim(x,'All responses above are directly supported by the general FAQ evidence provided.','Every preceding statement is supported by the general FAQ.',[(1,'There is no separate scholarship application process.'),(2,'CDS offers a limited number of tuition scholarships')],citations=[],verdict='insufficient',
      reason='The no-separate-application statement is present only in the supplied admissions FAQ. The explicit all-general-FAQ attribution is not supported. This is a source attribution failure, not an invented scholarship policy.')
reviews[x]['findings'].append('All three requested reference points remain correct, but the extra application-process fact cites the wrong FAQ and the concluding all-general-FAQ attribution is unsupported. This definite citation failure independently fails the frozen gates.')

x='accept-unspecified-api-error'
claim(x,'the content block type search_result is "Not Supported" in the list of message fields','The guide marks search_result content Not Supported.',[(1,r'| content | array, type = "search\_result" |  | Not Supported |')])
reviews[x]['findings'].append('Inspected all supplied excerpts: no specific HTTP status or JSON error body. Answer explicitly withholds both; no unsupported runtime behavior is inferred. Missing-information acknowledgments count under abstention, not factual-claim support.')

x='accept-personal-study-approval'
claim(x,'The sources mention general policies around independent study and electives','Supplied sources describe general degree policies.',[(1,'MSDS students can apply up to 6 credits of independent study'),(2,'DS-GA 1010 Independent Study')])
claim(x,'MSDS students can apply up to 6 credits of independent study (DS-GA 1010) to the degree','Up to six independent-study credits count.',[(1,'MSDS students can apply up to 6 credits of independent study')])
claim(x,'the course exists as an elective','DS-GA 1010 is listed among elective options.',[(2,'DS-GA 1010 Independent Study')])
reviews[x]['findings'].append('All supplied excerpts inspected. No personal approval status, supervisor identity or contact guidance is invented. Missing-information statements are assessed under abstention.')

if __name__=='__main__':
    assert not (DIR/'manual-review.json').exists()
    for identity,r in reviews.items():
        r['points']=[{'reference':p,'correctness':score,'present':True} for p,score in zip(cases[identity]['expected_answer_points'],r.pop('point_scores'),strict=True)]
        r['pass']=all(p['correctness']==2 for p in r['points']) and all(c['verdict']=='supported' and c['citation_verdict']=='supported' for c in r['claims'])
        r['citation_association_note']='Same paragraph/list-item association rule as baseline; unrelated citations are not assigned to every clause. Missing-information statements assessed under abstention.'
    write_json(DIR/'manual-review.json',list(reviews.values()))
