"""Record the complete metric inventory and per-case diagnostics for this series."""

import json
import math
from pathlib import Path
import statistics
import sys


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def measured(value, method, n, artifact):
    return {'status': 'measured', 'value': value, 'method': method, 'n': n, 'artifact': artifact}


def missing(reason, applicable=True):
    return {'status': 'unavailable' if applicable else 'not_applicable', 'value': None, 'reason': reason}


def timing(values):
    values = sorted(values)
    return {'mean': statistics.mean(values), 'p50': values[math.ceil(len(values) * .5) - 1],
            'p95': values[math.ceil(len(values) * .95) - 1], 'unit': 'seconds'}


def summarize(root):
    rows = read_rows(root / 'answers.jsonl')
    judge_path = root / ('judge-validated.jsonl' if (root / 'judge-validated.jsonl').exists() else 'judge.jsonl')
    judges = read_rows(judge_path)
    cases = {c['id']: c for c in json.loads((root / 'cases.json').read_text())}
    frozen = read_rows(root / 'frozen-evidence.jsonl')
    files = json.loads((root / 'chunks.json').read_text())
    rankings = []
    for original in frozen:
        case = cases[original['case_id']]
        if not case['answerable']:
            continue
        gold = {c['chunk_id'] for f in files for c in f['chunks'] if any(
            Path(e['file']).name == f['file']['file_name']
            and c['start_offset'] < e['end_offset'] and c['end_offset'] > e['start_offset']
            for e in case['evidence'])}
        selected = [c['chunk_id'] for c in original['answer']['retrieval']['candidates']][:5]
        rel = [int(identity in gold) for identity in selected]
        dcg = sum(v / math.log2(i + 2) for i, v in enumerate(rel))
        ideal = sum(1 / math.log2(i + 2) for i in range(min(5, len(gold))))
        rankings.append({'case_id': case['id'], 'gold_overlap_child_ids': sorted(gold),
                         'selected_ids': selected, 'recall_at_5': sum(rel) / len(gold),
                         'precision_at_5': sum(rel) / 5, 'hit_rate_at_5': int(any(rel)),
                         'mrr_at_5': next((1 / (i + 1) for i, v in enumerate(rel) if v), 0),
                         'ndcg_at_5': dcg / ideal})
    quality = {mode: [j for j in judges if j['strategy'] == mode and j['status'] == 'ok']
               for mode in ['baseline', 'candidate']}
    output = {}
    for mode in ['baseline', 'candidate']:
        all_rows = [r for r in rows if r['strategy'] == mode]
        good = [r for r in all_rows if r['status'] == 'ok']
        metrics = {}
        for key in ['recall_at_5', 'precision_at_5', 'hit_rate_at_5', 'mrr_at_5', 'ndcg_at_5']:
            metrics[key] = measured(statistics.mean(r[key] for r in rankings),
                'Frozen selected child top-5, binary nonempty gold-span overlap proxy. '
                'Unannotated children count as zero; annotations are not exhaustive semantic relevance labels. '
                'MRR truncated at 5; NDCG binary gains/log2 discount; precision denominator 5.',
                len(rankings), 'ranking-diagnostics.json')
        metrics['final_evidence_coverage'] = measured({key: statistics.mean(
            r['coverage'][key] for r in good if r['coverage'][key] is not None)
            for key in ['annotated_char_recall', 'full_evidence_recall']},
            'Frozen exact packed evidence; macro-average over answerable cases.',
            sum(c['answerable'] for c in cases.values()), 'frozen-evidence.jsonl')
        for key in ['answer_correctness', 'faithfulness', 'answer_completeness',
                    'answer_relevance', 'citation_support', 'citation_coverage', 'abstention']:
            metrics[key] = missing('Not assessed for all answers in this run; see focused development review.')
        valid = quality[mode]
        if valid:
            metrics['answer_correctness'] = measured(statistics.mean(
                statistics.mean(j['rating']['point_scores']) / 2 for j in valid),
                'Existing judge protocol: expected-point 0/1/2 scores normalized, macro-average. '
                'Combines correctness and partial completeness; valid judged subset only.', len(valid), 'judge.jsonl')
            metrics['answer_completeness'] = measured(statistics.mean(
                sum(p == 2 for p in j['rating']['point_scores']) / len(j['rating']['point_scores']) for j in valid),
                'Fraction of expected points scored fully correct and complete; macro-average, valid subset.',
                len(valid), 'judge.jsonl')
            for key, field in [('faithfulness', 'groundedness'), ('citation_support', 'citation_support')]:
                applicable = [j for j in valid if j['rating'][field] is not None]
                metrics[key] = measured(statistics.mean(j['rating'][field] / 2 for j in applicable),
                    'Minimum claim score per answer, 0/1/2 normalized; macro-average valid applicable reviews. '
                    'Quote validation verifies provenance, not semantic judgment.', len(applicable), 'judge.jsonl')
            claims = [c for j in valid for c in j['assessment']['claims']]
            if claims:
                metrics['citation_coverage'] = measured(sum(c['citation_support'] == 2 for c in claims) / len(claims),
                    'Micro-average fraction of judge-enumerated factual claims with fully supporting citations; '
                    'claim-free answers excluded. Depends on judge claim coverage.', len(claims), 'judge-validated.jsonl')
            else:
                for key in ['faithfulness', 'citation_support', 'citation_coverage']:
                    metrics[key] = missing('All provenance-valid reviews omitted factual claims; default aggregate scores '
                                           'are not semantic evidence. See Codex focused review; no full-run score.')
            unanswerable = [j for j in valid if not cases[j['case_id']]['answerable']]
            metrics['abstention'] = measured({
                'appropriate_unanswerable': sum(j['rating']['abstention'] == 2 for j in unanswerable) / len(unanswerable),
                'unanswerable_n': len(unanswerable),
                'incorrect_answerable': None,
                'incorrect_answerable_status': 'unavailable; protocol does not label answerable refusals'},
                'Existing judge protocol; separate answerable refusal audit required.', len(unanswerable), 'judge.jsonl')
        for key, field in [('first_answer_delta_latency', 'first_delta_seconds'),
                           ('complete_response_latency', 'total_seconds')]:
            metrics[key] = measured(timing([r[field] for r in good]),
                'Generation-only SDK stream; seconds, nearest-rank percentiles, successful requests. '
                'Full application end-to-end timing excluded.', len(good), 'answers.jsonl')
        metrics['stage_latency'] = {
            'generation': measured(timing([r['total_seconds'] for r in good]),
                                   'Production generation stage replay, including provider HTTP.', len(good), 'answers.jsonl'),
            'query_embedding_search_reranking_packing': missing('Frozen replay; these stages were not executed.', False)}
        usage = [r['usage'] for r in good if r['usage'] is not None]
        metrics['token_usage_and_cost'] = {
            'provider_usage': measured({key: sum(u[key] for u in usage) for key in ['input_tokens', 'output_tokens', 'total_tokens']},
                                      'Provider-reported generation usage totals.', len(usage), 'answers.jsonl'),
            'billed_cost': missing('Billing data not exposed by the response; no price estimate substituted.'),
            'local_rerank_compute': missing('No reranker execution in frozen replay.', False)}
        metrics['reliability'] = measured({
            'success': len(good), 'errors': len(all_rows) - len(good), 'attempts': len(all_rows),
            'success_rate': len(good) / len(all_rows), 'retries': 0,
            'timeouts': sum('Timeout' in r.get('error_type', '') for r in all_rows)},
            'All generation requests; SDK retries disabled.', len(all_rows), 'answers.jsonl')
        metrics['concurrency_and_throughput'] = measured({
            'concurrency': 1, 'successful_requests_per_active_second': len(good) / sum(r['total_seconds'] for r in all_rows)},
            'Sequential completed requests divided by active request time per arm, excluding gaps; '
            'not capacity under load. batch.json retains full mixed-arm wall time.', len(all_rows), 'answers.jsonl')
        metrics['ingestion_and_index'] = missing('No ingestion, index mutation, update or delete in this generation replay.', False)
        output[mode] = metrics
    pairs = []
    for case_id in cases:
        pair = [next(r for r in rows if r['case_id'] == case_id and r['strategy'] == mode)
                for mode in ['baseline', 'candidate']]
        assert pair[0]['sources'] == pair[1]['sources']
        assert pair[0]['messages'][1] == pair[1]['messages'][1]
        pairs.append({'case_id': case_id, 'identical_sources_and_user_message': True})
    for name, data in [('metrics.json', output), ('ranking-diagnostics.json', rankings), ('input-audit.json', pairs)]:
        with (root / name).open('x') as stream:
            json.dump(data, stream, indent=2)
    print(root.name, 'metrics recorded; judged', {k: len(v) for k, v in quality.items()})


if __name__ == '__main__':
    summarize(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent)
