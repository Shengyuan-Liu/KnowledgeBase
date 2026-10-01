"""Verify frozen inputs, recorded outcomes, measurements, and documentation links offline."""
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

from knowledgebase.config import Settings
from knowledgebase.rag.pdf_models import PdfExtraction
from clone_index import SOURCE, manifest
from record_check import METRICS

ROOT = Path(__file__).resolve().parent


def read(name):
    return json.loads((ROOT / name).read_text())


def main():
    preparation = read('preparation.json')
    execution = read('answer-execution-manifest.json')
    for name, digest in preparation['production_hashes'].items():
        assert sha256(Path(name).read_bytes()).hexdigest() == digest
    for name, digest in preparation['frozen_inputs'].items():
        assert sha256(Path(name).read_bytes()).hexdigest() == digest
    for name, digest in preparation['harness_hashes'].items():
        assert sha256((ROOT / name).read_bytes()).hexdigest() == digest
    for name, digest in execution['harness_hashes'].items():
        assert sha256((ROOT / name).read_bytes()).hexdigest() == digest
    assert not subprocess.check_output(['git', 'diff', 'HEAD', '--', 'knowledgebase'], text=True)
    assert subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip() == 'v2'
    print('Frozen product, protocol, cases, references, labels and executed harness hashes match.')

    assert manifest(SOURCE) == read('index-reuse.json')['source_file_hashes']
    for name, digest in execution['baseline_input_hashes'].items():
        assert sha256((ROOT.parent/'20260929-pdf-heading-acceptance'/name).read_bytes()).hexdigest() == digest
    indexed = {d['file']['file_id']: PdfExtraction.model_validate(d['extraction']) for d in read('index-snapshot.json')['files']}
    cases = read('frozen-cases.json')['cases']
    reference_hashes = {d['file']: d['sha256'] for d in read('frozen-cases.json')['corpus']}
    for case in cases:
        answer = read(case['id'] + '-planned.json')
        assert answer['status'] == 'completed'
        deltas = [e for e in answer['events'] if e['data']['event'] == 'answer_delta' and e['data'].get('delta')]
        assert ''.join(e['data']['delta'] for e in deltas) == answer['answer']['answer']
        assert answer['first_answer_delta_seconds'] == deltas[0]['seconds']
        assert answer['first_answer_delta_seconds'] <= answer['complete_response_seconds']
        assert answer['history_matches'] and answer['history_sources_shared_fields_match'] and answer['history_retrieval_matches']
        assert answer['answer']['retrieval']['evidence_tokens'] <= 4096
        for source in answer['answer']['sources']:
            extraction = indexed[source['file_id']]
            assert source['text'] == extraction.text[source['start_offset']:source['end_offset']]
            assert source['pdf']['revision_id'] == extraction.revision_id
            assert source['pdf']['regions'] == [r.model_dump(mode='json') for r in extraction.locate(source['start_offset'], source['end_offset'])]
            for supplement in source['pdf']['supplements']:
                assert supplement['text'] == extraction.text[supplement['start_offset']:supplement['end_offset']]
            assert source['file_id'] in answer['request']['file_ids']
            assert source['pdf']['source_hash'] == reference_hashes[source['file_name']]
    print('Six streamed answers reconstruct exactly; timing, source scope/hash and persisted history match.')

    review = read('review.json')
    diagnostics = read('diagnostics.json')
    measurement = read('measurement.json')['metric_inventory']
    assert set(measurement) == set(METRICS)
    for metric in measurement.values():
        assert metric['status'] in {'measured','unavailable','not_applicable'}
        for field in ['value','unit','sample_count','population','method','artifact','aggregation']:
            assert field in metric
        for artifact in metric['artifact'].split('; '):
            assert (ROOT/artifact).exists()
    assert sum(r['passed'] for r in review['cases']) == 6
    assert sum(p['correct'] for r in review['cases'] for p in r['expected_points']) == 16
    assert sum(len(r['expected_points']) for r in review['cases']) == 16
    assert sum(len(r['claims']) for r in review['cases']) == 19
    assert diagnostics['summary']['final_evidence_coverage'] == {'covered': 16, 'expected': 16}
    observations = [json.loads(line) for line in (ROOT / 'server-observations.jsonl').read_text().splitlines()]
    starts = [o for o in observations if o['kind'] == 'sdk_start']
    terminals = [o for o in observations if o['kind'] in {'sdk_complete', 'sdk_stream_terminal', 'sdk_error'}]
    assert len(starts) == len(terminals) == 39
    assert {o['call_id'] for o in starts} == {o['call_id'] for o in terminals}
    response_usage = [o.get('result', o.get('event', {}).get('response', {})).get('usage') for o in terminals]
    assert sum(u.get('input_tokens', 0) for u in response_usage) == 64483
    assert sum(u.get('output_tokens', 0) for u in response_usage) == 3493
    assert sum(u.get('prompt_tokens', 0) for u in response_usage) == 480
    assert all(o['kind'] != 'sdk_error' for o in terminals)
    token_metric = measurement['Token usage and cost']['value']
    assert token_metric['local_compute']['reranker'] == read('resolved-runtime.json')['reranker']
    assert token_metric['billed_cost']['value'] is None
    assert token_metric['by_role']['query_embedding']['cached_input_tokens'] is None
    assert read('measurement-check.json')['exit_code'] == 0
    assert review['summary']['citation_coverage'] == {'supported_citations':19, 'citation_required_claims':19}
    controller = read('controller-review.json')
    assert controller['before']['summary']['supported_without_irrelevant_selections'] == 3
    assert controller['after']['summary']['supported_without_irrelevant_selections'] == 8
    assert controller['after']['summary']['irrelevant_reference_instances'] == 0
    for arm in ['before', 'after']:
        for row in controller[arm]['rows']:
            assert sha256((ROOT.parent/row['artifact']).read_bytes()).hexdigest() == row['artifact_sha256']
    for row in review['cases']:
        assert sha256((ROOT/row['artifact']).read_bytes()).hexdigest() == row['artifact_sha256']
    assert read('harness-tests.json')['counts']['passed'] == 2
    assert read('server-stop.json')['baseline_directory_unchanged']
    print('Quality denominators, all 20 metrics, SDK usage and citation/controller reviews match raw evidence.')

    for path in [ROOT / 'README.md', ROOT / 'protocol.md', Path('docs/v2/README.md')]:
        text = path.read_text()
        assert not re.search('[\u4e00-\u9fff]', text)
        assert all(line.rstrip() == line for line in text.splitlines())
        for link in re.findall(r'\]\(([^)]+)\)', text):
            if not re.match(r'https?://', link) and not link.startswith('#'):
                assert (path.parent / link.split('#')[0]).exists(), (path, link)
    for name in ['answers-run','diagnostics-check','answer-review-check','controller-review-check','measurement-check','server-stop-check']:
        assert read(name+'.json')['exit_code'] == 0
    for flag in ['port_closed','ownership_lock_released','historical_rows_preserved','indexed_database_tables_unchanged']:
        assert read('server-stop.json')[flag]
    for case in cases:
        assessment = read(case['id']+'-planned.json')['answer']['retrieval']['planning']['assessment']['record']
        assert assessment['prompt_version'] == 'evidence-sufficiency-v6'
        assert assessment['input_token_count'] <= assessment['max_input_tokens'] == 8192
    credential = Settings().openai_api_key.encode()
    assert credential
    for path in ROOT.rglob('*'):
        if path.is_file() and path.suffix in {'.py', '.md', '.json', '.jsonl', '.log'}:
            assert credential not in path.read_bytes(), 'Credential must never appear in retained artifacts.'
    print('English documentation, local links, formatting and credential exclusion reviewed.')
    print('4 passed')


if __name__ == '__main__':
    main()
