"""Retain explicit Codex review of both attempts without editing raw answers."""
import json
from pathlib import Path
from evals.evaluate import digest, read_jsonl, write_json

DIR = Path(__file__).parent
RECOVERY = DIR.parent / '20260925-scope-timeout-recovery'


def review(directory):
    answers = {a['case_id']: a for a in read_jsonl(directory / 'answers.jsonl')}
    cases = {c['id']: c for c in json.loads((directory / 'cases.json').read_text())}
    originals = {c['id']: c for c in json.loads((directory / 'original-cases.json').read_text())}
    reviews = {}
    for identity, a in answers.items():
        case = cases[identity]
        reviews[identity] = {
            'case_id': identity, 'reviewer': 'Codex implementer; not independent human review',
            'answer_sha256': digest(a['answer'].encode()), 'service_status': a['status'],
            'claims': [], 'points': [{'reference': p, 'correctness': 2, 'present': True}
                                     for p in case['expected_answer_points']],
            'relevance': 2, 'abstains': not case['answerable'],
            'appropriate_abstention': not case['answerable'] and a['status'] == 'ok',
            'incorrect_abstention': False, 'language_compliance': True,
            'named_source_compliance': True, 'findings': [],
        }

    def claim(identity, answer_quote, source_id, needle, reason=None):
        a = answers[identity]
        assert answer_quote in a['answer']
        s = next(s for s in a['sources'] if s['source_id'] == source_id)
        start = s['text'].index(needle)
        left = s['text'].rfind('\n\n', 0, start) + 2
        if left == 1:
            left = 0
        right = s['text'].find('\n\n', start + len(needle))
        if right < 0:
            right = len(s['text'])
        claims = reviews[identity]['claims']
        claims.append({'id': f'c{len(claims)+1}', 'answer_quote': answer_quote,
            'statement': answer_quote, 'verdict': 'supported', 'citation_verdict': 'supported',
            'associated_citations': [source_id],
            'reason': reason or 'The cited supplied excerpt supports this claim and its qualifications.',
            'evidence': [{'source_id': source_id, 'file_name': s['file_name'],
                'start_offset': s['start_offset'] + left, 'end_offset': s['start_offset'] + right,
                'quote': s['text'][left:right]}]})

    if directory == DIR:
        x = 'accept-load-hours'
        for q, n in [('Full-time CDS students register for 9 credits', 'Full-time CDS students register for 9 credits.'),
                     ('Part-time students register for less than 9 credits', 'Part-time students register for less than 9 credits.'),
                     ('Students should plan on spending 10-15 hours per week per data science course, assuming they have all the prerequisites', 'Students should plan on spending 10-15 hours per week')]:
            claim(x, q, 1, n)
        x = 'accept-independent-passfail'
        claim(x, 'Up to 6 credits of independent study (DS-GA 1010) can be applied to the MSDS degree', 1, 'MSDS students can apply up to 6 credits of independent study')
        for q in ['Only 1 elective (not including the “One Data Science Elective” requirement) and DS-GA 1009 can be counted as pass/fail toward the MSDS degree',
                  'Required courses for the degree cannot be taken as pass/fail',
                  'Students in the Industry Concentration can use their 1 elective pass/fail allowance for an Industry Concentration elective']:
            claim(x, q, 1, 'Only 1 elective (this does not include')
        x = 'accept-course-two-areas'
        for q in ['DS-GA 1012 is listed under both the Big Data and Natural Language Processing subject areas',
                  'Large Language Models: Evaluation and Applications (formerly Natural Language Understanding and Computational Semantics)']:
            claim(x, q, 1, cases[x]['evidence'][0]['quote'])
        x = 'accept-awards-jobs'
        for q in ['Applicants are considered for tuition scholarships on a competitive basis',
                  'all applicants for admission are automatically considered for these awards',
                  'Scholarship recipients are notified in their admit letter']:
            claim(x, q, 1, 'CDS offers a limited number of tuition scholarships',
                  'The general FAQ says all admission applicants are considered competitively and recipients are notified in their admit letter. Automatically considered paraphrases all applicants; it does not assert a separate-application policy.')
        for q in ['An on-campus research or teaching position is not guaranteed',
                  'such opportunities are available but are competitive and typically posted on a semester-by-semester basis']:
            claim(x, q, 1, 'On-campus positions are available at CDS and NYU')
        reviews[x]['findings'].append('Requested v2 facts are complete and restricted to General FAQ. Original rubric scholarship-count detail is omitted; retain that partial original score.')
        x = 'accept-beta-header-scope'
        claim(x, 'the anthropic-beta header is ignored for the /messages endpoint, but is required (with the value files-api-2025-04-14) for Files API endpoints', 2, '| anthropic-beta | Ignored for `/messages`;')
        claim(x, 'The anthropic-version header is ignored', 2, '| anthropic-version | Ignored |')
        x = 'accept-message-subfields'
        for q, n in [('For text content citations (content | array, type="text" | citations): Support status is Ignored', r'| content | array, type="text" | citations | Ignored |'),
                     ('For tool_use id (content | array, type = "tool_use" | id): Support status is Fully Supported', r'| content | array, type = "tool\_use" | id | Fully Supported |'),
                     ('For tool_result is_error (content | array, type = "tool_result" | is_error): Support status is Ignored', r'| content | array, type = "tool\_result" | is\_error | Ignored |')]:
            claim(x, q, 1, n)
        x = 'accept-unspecified-api-error'
        reviews[x]['points'][0].update(correctness=1, present=True)
        reviews[x]['findings'].append('FAIL: the partial output starts with an appropriate absence statement but stops mid-quote when generation times out. Partial diagnostic credit only; no complete answer or supported positive status claim. The later recovery is a separate attempt.')
        x = 'accept-personal-study-approval'
        reviews[x]['findings'].append('Both personal facts explicitly withheld; no invented supervisor, approval or contact advice. Citations on absence statements are not positive factual claims.')
        x = 'scope-compare-faqs'
        claim(x, 'The "Master’s in Data Science: FAQ (Admissions)" page explicitly states that "There is no separate scholarship application process.', 1, 'There is no separate scholarship application process.',
              'The passage contains this policy. Source [1] document_labels identifies FAQ (Admissions); General FAQ is also supplied as [2]. Identity metadata is reviewed separately from raw excerpt offsets.')
        claim(x, 'Scholarship recipients will be notified in their admit letter', 1, 'There is no separate scholarship application process.')
        reviews[x]['points'][1].update(correctness=0, present=False)
        reviews[x]['findings'].append('Source attribution is now correct and both annotated FAQ spans are supplied (100%, previously 50%). The answer directly identifies the requested page, but does not explicitly state that General FAQ lacks the sentence. Preserve the frozen second expected point as missing; do not silently relax it to implied contrast. No opposite application requirement is invented.')
        for x in ['scope-ambiguous-faq', 'scope-missing-file']:
            reviews[x]['findings'].append('Correct deterministic clarification, empty sources, no query embedding or generation. Filename listings describe library state, not external claims requiring source citations.')
    else:
        x = 'accept-unspecified-api-error'
        claim(x, 'the content block type "search_result" is "Not Supported"', 1, r'| content | array, type = "search\_result" |  | Not Supported |')
        reviews[x]['findings'].append('Complete abstention on both exact HTTP status and JSON payload, with a supported extra support-status claim. Repeated absence statements are scored as abstention, not positive source claims. This recovery does not replace the failed attempt.')

    for identity, r in reviews.items():
        if identity in originals:
            scores = [p['correctness'] for p in r['points']]
            if identity == 'accept-awards-jobs':
                scores = [1, 2, 2]
            r['original_rubric_points'] = [dict(reference=p, correctness=v, present=v > 0)
                for p, v in zip(originals[identity]['expected_answer_points'], scores, strict=True)]
        r['pass'] = r['service_status'] == 'ok' and all(p['correctness'] == 2 for p in r['points']) and all(c['verdict'] == 'supported' and c['citation_verdict'] == 'supported' for c in r['claims'])
    assert not (directory / 'manual-review.json').exists()
    write_json(directory / 'manual-review.json', list(reviews.values()))
    lines = ['# Exact answers and source review', '',
             'Reviewer: Codex implementer, not independent human review. Frozen PLAN.md and expected points apply; raw answers are unchanged.', '']
    for identity, r in reviews.items():
        a = answers[identity]
        lines += ['## ' + identity, '', a['question'], '', '### Unedited answer', '', a['answer'], '',
                  '### Review', '', f"Strict case: {'PASS' if r['pass'] else 'FAIL'}; service: {a['status']}.", '']
        lines += ['- ' + f for f in r['findings']] + ['']
        for p in r['points']:
            lines += [f"- Required point ({p['correctness']}/2, present={p['present']}): {p['reference']}"]
        lines += ['']
        for c in r['claims']:
            lines += [f"**{c['id']}** supported; cited source {c['associated_citations']}.", '', '> ' + c['answer_quote'], '', c['reason'], '']
            for e in c['evidence']:
                lines += [f"`{e['file_name']}` characters {e['start_offset']}:{e['end_offset']}:", '', '```text', e['quote'], '```', '']
    (directory / 'REVIEW.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    review(DIR)
    review(RECOVERY)
