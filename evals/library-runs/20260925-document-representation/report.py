"""Summarize retained observations; never sample, repair output, or overwrite a run."""
from copy import deepcopy
import json
from pathlib import Path
from statistics import mean
from evals import metrics
from evals.evaluate import digest, read_jsonl, write_json

DIR = Path(__file__).parent
RECOVERY = DIR.parent / '20260925-scope-timeout-recovery'


def report(directory):
    cases = json.loads((directory / 'cases.json').read_text())
    answers = read_jsonl(directory / 'answers.jsonl')
    calls = read_jsonl(directory / 'calls.jsonl')
    meta = json.loads((directory / 'run.json').read_text())
    reviews = json.loads((directory / 'manual-review.json').read_text())
    rows = deepcopy(answers)
    for a in rows:
        if a['status'] == 'ok':
            for key in ('retrieval_seconds', 'scope_seconds'):
                a[key] = a['retrieval'].get(key)
    result = metrics.summarize(cases, rows, [], meta, calls)
    m = result['metrics']
    claims = [c for r in reviews for c in r['claims']]
    points = [p for r in reviews for p in r['points']]

    def score(key, values, method):
        m[key] = metrics.measured(mean(values), 'fraction', len(values), method, 'manual-review.json') if values else metrics.missing('No applicable reviewed observations in this workload.', False)

    score('answer_correctness', [p['correctness']/2 for p in points], 'Micro-average frozen required points, 0/1/2; incomplete transport output receives only partial diagnostic credit, never a passing case.')
    score('fully_correct_points', [p['correctness'] == 2 for p in points], 'Fraction of frozen required points fully correct; missing comparison point stays missing.')
    score('answer_completeness', [p['present'] for p in points], 'Required points addressed, separate from correctness and completed service delivery.')
    score('faithfulness', [c['verdict'] == 'supported' for c in claims], 'Inventoried factual claim occurrences; absence statements evaluated as abstention. Review includes the retained partial output.')
    score('citation_support', [c['citation_verdict'] == 'supported' for c in claims for _ in c['associated_citations']], 'Semantic support of associated claim/citation pairs, not ID validity.')
    score('citation_coverage', [bool(c['associated_citations']) and c['citation_verdict'] == 'supported' for c in claims], 'Factual claims with local supporting citations; claim-free abstentions and deterministic clarifications exempt.')
    score('answer_relevance', [r['relevance']/2 for r in reviews], '0 off-topic, 1 extraneous, 2 responsive. Responsiveness does not establish completeness or service completion.')
    by = {c['id']: c for c in cases}
    no = [r for r in reviews if not by[r['case_id']]['answerable']]
    yes = [r for r in reviews if by[r['case_id']]['answerable']]
    score('appropriate_abstention', [r['appropriate_abstention'] for r in no], 'Unanswerable cases including unresolved scope; a transport-interrupted answer does not pass.')
    score('incorrect_abstention', [r['incorrect_abstention'] for r in yes], 'Unjustified abstention among answerable questions.')
    score('answerable_refusal', [r['abstains'] for r in yes], 'Full or partial refusal among answerable questions.')
    score('personal_error_abstention', [r['appropriate_abstention'] for r in no if not r['case_id'].startswith('scope-')], 'Personal/API-error unavailable facts, excluding document clarifications.')
    score('scope_clarification', [r['appropriate_abstention'] for r in no if r['case_id'].startswith('scope-')], 'Ambiguous/missing document requests, with no provider calls.')
    score('functional_case_pass_rate', [r['pass'] for r in reviews], 'Frozen strict required-point and source gates AND service completion; retain failures.')
    score('english_compliance', [r['language_compliance'] for r in reviews], 'Manual full-output review, including retained partial answer.')
    score('named_source_compliance', [r['named_source_compliance'] for r in reviews], 'Attribution against exact file identities; separate from omitted answer points.')
    original = [p for r in reviews for p in r.get('original_rubric_points', [])]
    score('original_rubric_correctness', [p['correctness']/2 for p in original], 'Historical rubric retained separately; not the revised acceptance denominator.')
    m['claim_count'] = metrics.measured(len(claims), 'claims', len(reviews), 'All explicit reviewed factual claim occurrences.', 'manual-review.json')
    m['unsupported_claims'] = metrics.measured(sum(c['verdict'] != 'supported' for c in claims), 'claims', len(reviews), 'Full reviewed claim inventory.', 'manual-review.json')
    m['contradicted_claims'] = metrics.missing('Support sufficiency reviewed; no independent contradiction taxonomy.')
    for key in ('strict_pass_rate', 'judge_seconds', 'judge_reliability'):
        m[key] = metrics.missing('No paid judge; use explicit Codex functional_case_pass_rate and source review.', False)
    for stage in ('judge', 'ingestion'):
        m['token_usage'][stage] = metrics.missing('No calls for this stage; verified closed baseline index reused.', False)
    for key, reason in [('model_loading', 'Local reranking disabled; no local inference model loaded.'),
                        ('rerank_seconds', 'Reranking disabled.'),
                        ('ingestion', 'No fresh ingestion; source/index hashes and chunk snapshots verified against the baseline.'),
                        ('update_delete', 'This live pass queries a copied index; lifecycle checks are separate offline records.')]:
        m[key] = metrics.missing(reason, False)
    m['scope_seconds'] = metrics.timing([r.get('scope_seconds') for r in rows if r['status'] == 'ok'])
    m['scope_seconds'].setdefault('method', 'Identity lookup and resolution.')
    m['embedding_seconds'] = metrics.timing([c['seconds'] for c in calls if c['stage'] == 'query_embedding' and c['status'] == 'ok'])
    m['embedding_seconds'].update(artifact='calls.jsonl', method='All executed successful query embeddings, including the subsequently failed generation; skipped calls are not timed zeros. Median P50, nearest-rank P95.')
    for key in ('total_seconds', 'first_delta_seconds'):
        m[key]['method'] += ' Successful service observations only; includes deterministic clarifications when present, excludes HTTP/browser; queue/provider wait included.'
    m['attempt_duration_seconds'] = metrics.timing([a['total_seconds'] for a in answers])
    m['attempt_duration_seconds']['method'] = 'All attempts to terminal complete/error, including failure; this is not complete-answer latency. Median P50, nearest-rank P95.'
    failures = [a for a in answers if a['status'] != 'ok']
    for key in ('total_seconds', 'first_delta_seconds', 'generation_seconds', 'generation_first_delta_seconds'):
        entry = metrics.timing([a.get(key) for a in failures]) if failures else metrics.missing('No failed attempts in this recovery workload.', False)
        if entry['status'] == 'measured':
            entry['method'] = 'Failed attempt observations retained separately; total/generation stop at error, not complete answer. Median P50, nearest-rank P95.'
        m['failed_' + key] = entry
    m['concurrency_throughput']['method'] += ' Monotonic interval is authoritative; wall-clock timestamps span a longer unexplained interval and are not substituted for measured service durations.'
    generations = [c for c in calls if c['stage'] == 'generation']
    missing_usage = [c['call_id'] for c in generations if not c.get('usage')]
    m['missing_generation_usage'] = metrics.missing('Failed generation call(s) have no final provider usage: ' + ', '.join(missing_usage)) if missing_usage else metrics.measured(0, 'calls', len(generations), 'All generation calls have final reported usage.', 'calls.jsonl')
    result.update(reviewer='Codex implementer, not independent human review', review_protocol='PLAN.md',
                  cases=[dict(case_id=r['case_id'], service_status=r['service_status'], **{k:r[k] for k in ['pass', 'points', 'findings']}) for r in reviews])
    result['limitations'] += ['The full-suite first pass retains two slow completed generations and one stream timeout; recovery does not erase them.',
                             'Comparison source attribution is fixed, but its explicitly frozen General-FAQ absence point is not stated. No criteria were relaxed after output.'] if directory == DIR else ['Single failed-case recovery, not a repeat of the full suite.']
    completed = [a for a in answers if a['status'] == 'ok']
    scope_checks = []
    for a in completed:
        scope = a['retrieval'].get('document_scope')
        if scope:
            scope_checks.append({s['file_id'] for s in a['sources']} <= set(scope['file_ids']) and {c['file_id'] for c in a['retrieval']['candidates']} <= set(scope['file_ids']))
    observed_input = [c['usage']['input_tokens'] for c in generations if c.get('usage')]
    gates = {
        'all_requests_complete': len(completed) == len(cases),
        'all_manual_cases_pass': all(r['pass'] for r in reviews),
        'english': all(r['language_compliance'] for r in reviews),
        'scope_filter': all(scope_checks),
        'full_evidence_coverage': m['full_evidence_recall']['value'] == 1 if yes else None,
        'citation_ids': all(not a['citation_check']['invalid_source_ids'] for a in completed),
        'citation_coverage': m['citation_coverage']['value'] >= .8,
        'latency': m['total_seconds']['value']['mean'] <= 10 and m['total_seconds']['value']['p95'] <= 20 and m['first_delta_seconds']['value']['p95'] <= 10,
        'input_budget_observed': max(observed_input) <= 12000,
        'input_budget_complete_measurement': not missing_usage,
        'reused_index_verified': meta['chunk_units_sha256'] == json.loads((DIR.parent/'20260925-document-scope/run.json').read_text())['chunk_units_sha256'] if 'chunk_units_sha256' in json.loads((DIR.parent/'20260925-document-scope/run.json').read_text()) else digest((directory/'chunks.json').read_bytes()) == digest((DIR.parent/'20260925-document-scope/chunks.json').read_bytes()),
    }
    acceptance = dict(status='passed' if all(v is not False for v in gates.values()) else 'failed', gates=gates,
                      gate_notes={'full_evidence_coverage': 'Not applicable to the recovery unanswerable question; null is not zero recall.', 'ingestion': 'Fresh-ingestion gate not exercised, as frozen in PLAN.md; index copy verified instead.'},
                      cases_passed=sum(r['pass'] for r in reviews), cases_total=len(reviews),
                      paid_calls=len(calls), paid_generation_calls=len(generations), paid_judge_calls=0,
                      observed_max_input_tokens=max(observed_input), missing_usage_call_ids=missing_usage)
    assert not (directory/'metrics.json').exists() and not (directory/'acceptance.json').exists()
    write_json(directory/'metrics.json', result)
    write_json(directory/'acceptance.json', acceptance)
    (directory/'METRICS.md').write_text('# Complete metric inventory\n\n' + '\n'.join(metrics.console_lines(result)) + '\n')
    print(directory.name, json.dumps(acceptance), 'latency', m['total_seconds'], m['first_delta_seconds'])


if __name__ == '__main__':
    report(DIR)
    report(RECOVERY)
