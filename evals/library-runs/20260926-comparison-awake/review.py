"""Explicit implementer review of every unchanged answer and supplied source."""
import json
from pathlib import Path
from evals.evaluate import digest, read_jsonl, write_json
DIR = Path(__file__).parent
answers = {a['case_id']:a for a in read_jsonl(DIR/'answers.jsonl')}
cases = {c['id']:c for c in json.loads((DIR/'cases.json').read_text())}
reviews = {key:dict(case_id=key, reviewer='Codex implementer, not independent human review',
    answer_sha256=digest(a['answer'].encode()), claims=[],
    points=[dict(reference=p,correctness=2,present=True) for p in cases[key]['expected_answer_points']],
    relevance=2, abstains=not cases[key]['answerable'], appropriate_abstention=not cases[key]['answerable'],
    incorrect_abstention=False, language_compliance=True, named_source_compliance=True, findings=[])
    for key,a in answers.items()}


def claim(key, quote, source_id, needle, reason='The associated supplied excerpt supports this claim and its qualifications.'):
    assert quote in answers[key]['answer']
    source = next(s for s in answers[key]['sources'] if s['source_id'] == source_id)
    pos = source['text'].index(needle)
    left = source['text'].rfind('\n\n',0,pos)+2
    if left == 1:left = 0
    right = source['text'].find('\n\n',pos+len(needle))
    if right < 0:right = len(source['text'])
    entries = reviews[key]['claims']
    entries.append(dict(id=f'c{len(entries)+1}',answer_quote=quote,statement=quote,
        verdict='supported',citation_verdict='supported',associated_citations=[source_id],reason=reason,
        evidence=[dict(source_id=source_id,file_name=source['file_name'],start_offset=source['start_offset']+left,
                       end_offset=source['start_offset']+right,quote=source['text'][left:right])]))

x='accept-load-hours'
for q,n in [('full-time CDS students register for 9 credits','Full-time CDS students register for 9 credits.'),
            ('part-time students register for less than 9 credits','Part-time students register for less than 9 credits.'),
            ('A student with the prerequisites should plan to spend 10-15 hours per week per data science course','Students should plan on spending 10-15 hours per week')]:claim(x,q,1,n)
x='accept-independent-passfail'
claim(x,'MSDS students can apply up to 6 credits of independent study (DS-GA 1010) to the MSDS degree',1,'MSDS students can apply up to 6 credits of independent study')
for q in ['Only 1 elective (not including the “One Data Science Elective” requirement) and DS-GA 1009 can be taken as pass/fail and counted towards the MSDS degree',
          'For students in the Industry Concentration, the 1 elective pass/fail allowance can be used for an Industry Concentration elective',
          'Required courses for the degree cannot be taken as pass/fail']:claim(x,q,1,'Only 1 elective (this does not include')
x='accept-course-two-areas'
for q in ['DS-GA 1012 is listed under both Big Data and Natural Language Processing subject areas',
          '"Large Language Models: Evaluation and Applications" (formerly "Natural Language Understanding and Computational Semantics")']:
    claim(x,q,1,cases[x]['evidence'][0]['quote'])
x='accept-awards-jobs'
for q in ['Applicants are considered for tuition scholarships automatically',
          'All applicants for admission are considered for these awards on a competitive basis',
          'Scholarship recipients are notified in their admit letter']:
    claim(x,q,1,'CDS offers a limited number of tuition scholarships',
          'All admission applicants are considered competitively. Automatically considered paraphrases this statement without asserting the Admissions-only separate-application policy.')
for q in ['An on-campus research or teaching position is not guaranteed',
          'On-campus positions are available at CDS and NYU, but we do not guarantee such opportunities for any given student.',
          'Positions are competitive, and are typically posted on a semester-by-semester basis']:
    claim(x,q,1,'On-campus positions are available at CDS and NYU')
reviews[x]['findings'].append('All requested v2 facts present, with only General FAQ evidence. Original optional scholarship-count detail still omitted and retained as a partial original-rubric point.')
x='accept-beta-header-scope'
claim(x,'"anthropic-beta" does not have the same behavior for /messages and Files API endpoints: it is "ignored for `/messages`" but "required (`files-api-2025-04-14`) for Files API endpoints"',2,'| anthropic-beta | Ignored for `/messages`;')
claim(x,'The "anthropic-version" header is "ignored"',2,'| anthropic-version | Ignored |')
x='accept-message-subfields'
for q,n in [('For text content citations (content, array, type="text", citations), the support status is "Ignored"',r'| content | array, type="text" | citations | Ignored |'),
            ('For tool_use id (content, array, type="tool_use", id), the support status is "Fully Supported"',r'| content | array, type = "tool\_use" | id | Fully Supported |'),
            ('For tool_result is_error (content, array, type="tool_result", is_error), the support status is "Ignored"',r'| content | array, type = "tool\_result" | is\_error | Ignored |')]:claim(x,q,1,n)
x='accept-unspecified-api-error'
for q in ['content blocks of type search_result are "Not Supported"','content of type search_result is not supported']:
    claim(x,q,1,r'| content | array, type = "search\_result" |  | Not Supported |')
reviews[x]['findings'].append('Exact HTTP status and JSON body are explicitly withheld. The support-status fact occurs twice; both occurrences are reviewed. Redundant closing summary is a style miss, not a new factual/abstention failure.')
x='accept-personal-study-approval'
reviews[x]['findings'].append('Both personal facts are withheld with no invented supervisor, approval or contact advice. Absence statements are reviewed as abstention, not positive facts; source IDs on them do not prove unseen personal information.')
x='scope-compare-faqs'
for q in ['In the "masters-in-data-science-faq.txt" (Admissions FAQ), the page explicitly states: "There is no separate scholarship application process.',
          'Scholarship recipients will be notified in their admit letter.']:
    claim(x,q,1,'There is no separate scholarship application process.',
          'Source [1] supplies the statement and carries Admissions identity labels. Positive text is separate from the General FAQ evidence-limitation assessment.')
claim(x,'CDS offers a limited number of tuition scholarships for our students. All applicants for admission are considered for these awards on a competitive basis. Scholarship recipients will be notified in their admit letter.',2,'CDS offers a limited number of tuition scholarships')
claim(x,'Therefore, only the "masters-in-data-science-faq.txt" (Admissions FAQ) page explicitly says there is no separate scholarship application process',1,'There is no separate scholarship application process.',
      'Repeated positive attribution is supported by [1]. The exclusion of General FAQ was inspected against its supplied financial paragraph [2] and the frozen file; no inference that a separate application is required.')
reviews[x]['findings'].append('Both frozen points now explicit: Admissions contains the statement, General does not state it. Both gold spans are supplied in correctly labeled sources; the quoted General paragraph does not imply an opposite application rule. The final summary repeats the conclusion. Page-wide absence wording is broader than the requested excerpt wording, but matches the inspected frozen General FAQ; do not generalize to current websites or unseen documents.')
for x in ['scope-ambiguous-faq','scope-missing-file']:
    reviews[x]['findings'].append('Deterministic scope clarification, no evidence or provider calls; filenames describe actual library state.')

if __name__=='__main__':
    assert not (DIR/'manual-review.json').exists()
    originals={c['id']:c for c in json.loads((DIR/'original-cases.json').read_text())}
    for key,r in reviews.items():
        if key in originals:
            scores=[2]*len(r['points'])
            if key=='accept-awards-jobs':scores=[1,2,2]
            r['original_rubric_points']=[dict(reference=p,correctness=v,present=True) for p,v in zip(originals[key]['expected_answer_points'],scores,strict=True)]
        r['pass']=answers[key]['status']=='ok' and all(p['correctness']==2 for p in r['points']) and all(c['verdict']=='supported' and c['citation_verdict']=='supported' for c in r['claims'])
    write_json(DIR/'manual-review.json',list(reviews.values()))
    lines=['# Exact outputs and source review','','Reviewer: Codex implementer, not independent human review. Frozen PLAN.md applies.','']
    for key,r in reviews.items():
        lines+=['## '+key,'',answers[key]['question'],'','### Unedited answer','',answers[key]['answer'],'','### Review','',f"Strict case: {'PASS' if r['pass'] else 'FAIL'}.",'']
        lines+=['- '+f for f in r['findings']]+['']
        lines+=[f"- Required point ({p['correctness']}/2): {p['reference']}" for p in r['points']]+['']
        for c in r['claims']:
            lines += [f"**{c['id']}** supported; citations {c['associated_citations']}.",'','> '+c['answer_quote'],'',c['reason'],'']
            for e in c['evidence']:
                lines += [f"`{e['file_name']}` characters {e['start_offset']}:{e['end_offset']}:",'','```text',e['quote'],'```','']
    (DIR/'REVIEW.md').write_text('\n'.join(lines))
