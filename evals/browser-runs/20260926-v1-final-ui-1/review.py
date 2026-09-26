"""Retain Codex's explicit source review and derive diagnostics without API calls."""
import json
from pathlib import Path
from evals import metrics
from evals.evaluate import timestamp, write_json

p = Path(__file__).parent
if (p / 'review.json').exists():
    raise SystemExit('Review artifacts are append-only.')
a = json.loads((p / 'acceptance.json').read_text())
s = json.loads((p / 'storage-before-deletion.json').read_text())
run = json.loads((p / 'run.json').read_text())
fixtures = {f['name']: f['text'] for f in a['fixtures']}
general, access = fixtures['general-guide.txt'], fixtures['access-guide.md']
# The plan froze facts before generation; these character annotations are derived
# afterward for transparent diagnostic scoring, not a held-out ranking benchmark.
gold = [
    [('general-guide.txt', general.index('The lab opens'), general.index('\nOn weekends'))],
    [('general-guide.txt', general.index('On weekends'), len(general))],
    [('access-guide.md', access.index('Weekend visits'), len(access)), ('general-guide.txt', 0, len(general))],
]
claims = [
    [('the lab opens at 9 AM', 1, 'opens at 9 AM'), ('closes at 6 PM on weekdays', 1, 'closes at 6 PM on weekdays')],
    [('on weekends the lab opens at 10 AM', 1, 'On weekends, the lab opens at 10 AM'), ('closes at 2 PM', 1, 'closes at 2 PM')],
    [('Weekend visits require a confirmed reservation.', 1, 'Weekend visits require a confirmed reservation.'),
     ('Submit a reservation request at least 24 hours in advance', 1, 'Submit a reservation request at least 24 hours in advance'),
     ('does not mention any requirement for a reservation for weekend visits', 2, general),
     ('it only provides the weekend opening and closing times', 2, 'On weekends, the lab opens at 10 AM and closes at 2 PM.')],
]
chunks = [{**c, 'file_name': next(f['file_name'] for f in s['tables']['files'] if f['file_id'] == c['file_id'])} for c in s['tables']['chunks']]
reviews = []
for i, answer in enumerate(a['answers']):
    m = answer['saved']['messages'][-1]
    units = []
    for quote, citation, support in claims[i]:
        source = next(x for x in m['sources'] if x['source_id'] == citation)
        assert quote in m['content'] and support in source['text']
        units.append({'answer_quote': quote, 'citation_id': citation, 'source_file': source['file_name'],
            'source_quote': support, 'verdict': 'supported', 'citation_support': True,
            'review_note': 'Absence reviewed against the full tiny General fixture; weekend-only wording is interpreted within the question, not as denying its weekday information.' if i == 2 and citation == 2 else 'Exact source fact and document attribution match.'})
    evidence = [{'file': f, 'start_offset': start, 'end_offset': end} for f, start, end in gold[i]]
    for e in evidence:
        assert any(x['file_name'] == e['file'] and x['start_offset'] <= e['start_offset'] and x['end_offset'] >= e['end_offset'] for x in m['sources'])
    expected = [['Weekday opening is 9 AM', 'Weekday closing is 6 PM'],
                ['Weekend opening is 10 AM', 'Weekend closing is 2 PM'],
                ['Access explicitly requires a weekend reservation', 'General does not specify a weekend reservation requirement']][i]
    reviews.append({'question': answer['question'], 'claims': units, 'expected_points': [{'point': x, 'present': True, 'correctness': 2} for x in expected],
        'relevance': 2, 'abstains': False, 'strict_pass': True, 'gold_spans': evidence,
        'ranking': metrics.ranking({'answerable': True, 'evidence': evidence}, m['retrieval']['candidates'], chunks, 5),
        'full_evidence_coverage': 1.0})
review = {'reviewed_at': timestamp(), 'reviewer': 'Codex implementer; not independent human or separate API judge',
    'protocol': 'Frozen PLAN.md expected facts; manually inspect every factual claim and citation including extra details. Correctness 0/1/2, relevance 0/1/2. Strict pass requires all expected facts correct and present, every factual claim supported/cited, direct relevance, no refusal.',
    'scope': 'Three completed answers; cancelled turn excluded from answer quality and recorded separately in reliability.',
    'annotation_timing': 'Fact expectations frozen before calls. Exact source spans and child overlap labels derived afterward; diagnostic only.',
    'cases': reviews,
    'visual_review': {'screenshots': ['comparison-evidence.png', 'deleted-evidence.png'], 'result': 'Readable three-column desktop layout; comparison citations, heading/line locations and deleted historical label visible. No mobile/responsive coverage claimed.'},
    'transport_observer_correction': 'All four response.text() calls failed to provide bodies. The original harness hardcoded cancellation in the error, incorrectly including three completed requests. Cause was not captured; no conclusion about transport failure follows. Complete saved answers/evidence are verified. Future harness retains actual errors; no paid rerun.',
    'cancellation': 'Stop after Answering status; no proof that first answer text had arrived. No unfinished turn persisted.'}
write_json(p / 'review.json', review)
inv = run['metric_inventory'].copy()
for name in ('recall_at_k', 'precision_at_k', 'hit_rate_at_k', 'mrr_at_k', 'ndcg_at_k'):
    inv[name] = metrics.measured(sum(r['ranking'][name] for r in reviews) / 3, 'fraction', 3,
        'Selected pre-expansion top-5 children; post-run binary overlap with spans derived from frozen expected facts. Precision divides by K even with fewer results. Macro-average, misses zero; diagnostic labels are not exhaustive semantic relevance.', 'review.json')
for name in ('annotated_char_recall', 'full_evidence_recall'):
    inv[name] = metrics.measured(1.0, 'fraction', 3, 'All four annotated question-specific spans fully contained in actual supplied context; macro-average over questions. Span labels derived after run from frozen facts.', 'review.json')
for name in ('answer_correctness', 'answer_completeness', 'fully_correct_points', 'faithfulness', 'answer_relevance', 'citation_support', 'citation_coverage', 'strict_pass_rate', 'functional_case_pass_rate', 'english_compliance', 'named_source_compliance'):
    inv[name] = metrics.measured(1.0, 'fraction', 3, 'Codex manual review, macro-average over 3 answers. Six expected points, eight factual claims and eight supporting claim-citation pairs. Rubric and evidence in review.json; not independent accuracy.', 'review.json')
for name in ('incorrect_abstention', 'answerable_refusal'):
    inv[name] = metrics.measured(0.0, 'fraction', 3, 'No refusal in three answerable cases; cancelled turn is not an abstention.', 'review.json')
for name in ('unsupported_claims', 'contradicted_claims'):
    inv[name] = metrics.measured(0, 'claims', 8, 'Eight factual claim units manually inspected.', 'review.json')
inv['claim_count'] = metrics.measured(8, 'claims', 3, 'Two weekday, two weekend and four comparison claim units.', 'review.json')
for name in ('rerank_seconds', 'personal_error_abstention', 'scope_clarification', 'original_rubric_correctness'):
    inv[name] = metrics.missing('Disabled reranking, no personal-error/ambiguous-scope case, and no previous rubric in this new workflow.', False)
inv['scope_seconds'] = metrics.timing([x['saved']['messages'][-1]['retrieval']['scope_seconds'] for x in a['answers']])
inv['scope_seconds']['artifact'] = 'acceptance.json'
inv['reliability'] = metrics.measured({'workflow_pass': 1, 'workflow_fail': 0, 'workflow_skip': 0,
    'completed_answers': 3, 'answer_errors': 0, 'answer_timeouts': 0, 'intentional_cancellations': 1,
    'uploads_ready': 2, 'deletions_verified': 2, 'test_retries': 0, 'sdk_retries': 0,
    'raw_sse_body_observations_failed': 4, 'upstream_actual_counts': 'unavailable'}, 'outcomes', 1,
    'One sequential workflow, four user submissions: three complete and one intentionally cancelled. Body-observer failures are instrumentation gaps, not answer failures.', 'acceptance.json')
inv['runtime_warnings'] = metrics.measured({'browser_javascript_errors': 0, 'stream_finalizer_warnings_in_log': 0, 'node_color_configuration_warning': 1}, 'observed log counts', 1, 'Manual inspection of browser.log and acceptance browserErrors; not proof of absence in other runs.', 'browser.log')
write_json(p / 'reviewed-metrics.json', {'derived_at': timestamp(), 'basis': 'run.json + review.json; original artifacts retained', 'metric_inventory': inv})
print('Reviewed 3 answers, 6 expected points, 8 factual claims, 4 gold spans and 2 screenshots; all pass within recorded scope.')
