"""Matched local packing replay with immutable source-bound annotations."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
from time import perf_counter

from knowledgebase.rag.context import build_context
from knowledgebase.rag.packing import pack_evidence
from knowledgebase.rag.pdf_evidence import pdf_evidence
from knowledgebase.rag.pdf_models import PdfExtraction
from knowledgebase.schemas import RetrievedChunk, RetrievalDiagnostics, PdfTableSpan

ROOT = Path(__file__).parent
OLD = ROOT.parent / '20260927-table-context-scope'
LIVE = Path('evals/library-runs/20260927-table-context-scope-acceptance')
sys.path.insert(0, str(OLD))
from replay import load_module, make_inputs, read, tokens, write, source
from analyze_comparison import METRICS, measured, omitted, distribution
from financial_control import labels_for, coverage


def audit(evidence, context, extraction):
    """Check model-facing bindings against original cells independently of rendering."""
    total = 0
    for hit in evidence.chunks:
        assert hit.chunk.text == extraction.text[hit.chunk.start_offset:hit.chunk.end_offset]
        assert f'Excerpt:\n{hit.chunk.text}\nPDF physical pages:' in context
        for extra in hit.pdf.supplements:
            assert extra.text == extraction.text[extra.start_offset:extra.end_offset]
            assert extra.text in context
        for table in hit.pdf.tables:
            if getattr(table, 'reading', None) is None:
                continue
            assert table.reading in context
            original = next(b.table for b in extraction.blocks if b.table and b.table.table_id == table.table_id)
            data = [c for c in original.cells if not c.column_header and not c.row_header
                    and hit.chunk.start_offset <= c.start_offset and c.end_offset <= hit.chunk.end_offset
                    and c.start_offset < hit.chunk.end_offset and hit.chunk.start_offset < c.end_offset]
            pairs = [pair for line in table.reading.splitlines() for pair in json.loads(line.split('): ', 1)[1])]
            assert len(pairs) == len(data)
            for pair, cell in zip(pairs, sorted(data, key=lambda c: (c.row_start, c.row_end, c.column_start)), strict=True):
                assert pair[1] == (cell.text or None)
                assert cell.text == extraction.text[cell.start_offset:cell.end_offset]
                headers = sorted([h for h in original.cells if h.column_header and h.text.strip()
                    and h.column_start <= cell.column_start and cell.column_end <= h.column_end
                    and (original.columns == 1 or h.column_end - h.column_start < original.columns)], key=lambda h: (h.row_start,h.column_start))
                assert pair[0] == (' > '.join(' '.join(h.text.split()) for h in headers) or f'Column {cell.column_start}:{cell.column_end}')
                total += 1
    return total


def main():
    output = ROOT / sys.argv[1]
    assert not output.exists()
    output.mkdir()
    # Compatibility adapter removes the newly added default field from old rendering.
    class LegacyTableSpan(PdfTableSpan):
        def model_dump(self, **kwargs):
            kwargs["exclude"] = set(kwargs.get("exclude", set())) | {"reading"}
            return super().model_dump(**kwargs)
    baseline_pdf = load_module(ROOT / 'baseline-code/pdf_evidence.py', 'baseline_pdf')
    baseline_pdf.PdfTableSpan = LegacyTableSpan
    before_context = load_module(ROOT / 'baseline-code/context.py', 'before_context')
    before_packing = load_module(ROOT / 'baseline-code/packing.py', 'before_packing')
    before_packing.build_context = before_context.build_context
    before_packing.PDF_CONTEXT_FORMAT = before_context.PDF_CONTEXT_FORMAT
    import replay
    replay.FROZEN = LIVE
    frozen = read(LIVE / 'frozen-cases.json')
    index = read(LIVE / 'index-snapshot.json')
    observations = [json.loads(line) for line in (LIVE / 'server-observations.jsonl').read_text().splitlines()]
    dense = make_inputs(frozen, index, observations)['cases']
    labels = read(LIVE / 'frozen-fact-labels.json')['labels']
    metrics = load_module(LIVE / 'metrics/analyze.py', 'dense_metrics')
    financial_index = read(Path('evals/library-runs/20260927-v2-pdf-live/index-snapshot.json'))
    financial_doc = next(d for d in financial_index['files'] if d['file']['file_name'] == 'apple-fy24.pdf')
    financial_rows = read(OLD / 'financial-control-1/comparison.json')['rows']
    for row in dense:
        row['group'] = 'dense'
        row['document'] = index['files'][0]
        row['facts'] = row['case']['expected_fact_ids']
    all_inputs = dense
    for row in financial_rows:
        item = read(OLD / f"financial-control-1/{row['identity']}-inputs.json")
        all_inputs.append(dict(item, identity=row['identity'], group='financial', document=financial_doc, facts=row['requested_facts']))
    write(output / 'frozen-inputs.json', all_inputs)
    results = []
    for item in all_inputs:
        extraction = PdfExtraction.model_validate(item['document']['extraction'])
        result_row = dict(identity=item['identity'], group=item['group'], facts=item['facts'])
        for phase, pack, render, derive in [('before', before_packing.pack_evidence, before_context.build_context, baseline_pdf.pdf_evidence),
                                            ('after', pack_evidence, build_context, pdf_evidence)]:
            selected = [RetrievedChunk.model_validate(row) for row in item['selected']]
            expanded = [RetrievedChunk.model_validate(row) for row in item['expanded']]
            for hit in [*selected, *expanded]:
                hit.pdf = derive(extraction, hit.chunk.start_offset, hit.chunk.end_offset)
            start = perf_counter()
            evidence = pack(selected, expanded, RetrievalDiagnostics.model_validate(item['diagnostics']))
            elapsed = perf_counter() - start
            context = render(evidence.chunks)
            assert tokens(context) == evidence.diagnostics.evidence_tokens <= 4096
            if item['group'] == 'dense':
                checks = metrics.supplied_coverage([source(hit, n) for n, hit in enumerate(evidence.chunks, 1)],
                    item['facts'], labels, {item['document']['file']['file_id']: item['document']})
                covered = sum(f['fully_covered'] for f in checks['facts'])
            else:
                table_id, facts = labels_for(item['document']['extraction'])
                checks = coverage(evidence.model_dump(mode='json'), item['facts'], table_id, facts)
                covered = sum(checks[f]['complete'] for f in item['facts'])
                assert checks['apple_units']['complete']
            assert covered == len(item['facts']), (item['identity'], phase, checks)
            bound_cells = audit(evidence, context, extraction)
            write(output / f"{item['identity']}-{phase}.json", evidence.model_dump(mode='json'))
            write(output / f"{item['identity']}-{phase}.txt", context)
            result_row[phase] = dict(tokens=tokens(context), covered=covered, total=len(item['facts']),
                coverage=checks, packing_seconds=elapsed, audited_reading_cells=bound_cells,
                packed_ids=[h.chunk.chunk_id for h in evidence.chunks])
        results.append(result_row)
    inventory = {m: omitted('Local frozen packing replay; no new retrieval, answers, provider calls, ingestion or load test.') for m in METRICS}
    aggregate = {g: {phase: dict(covered=sum(r[phase]['covered'] for r in results if r['group']==g),
        total=sum(r[phase]['total'] for r in results if r['group']==g)) for phase in ['before','after']} for g in ['dense','financial']}
    inventory['Final evidence coverage'] = measured(aggregate, 'source-bound fact instances', 24,
        'Six dense and six financial contexts per phase', 'Exact canonical cells, row labels, grouped headers, period, page and units; explicit blanks require the complete row.', 'micro coverage by corpus')
    inventory['Token usage and cost'] = measured({r['identity']: {p:r[p]['tokens'] for p in ['before','after']} for r in results},
        'local cl100k_base context tokens',24,'Same frozen selections before and after','Complete rendered context; no provider usage or billing applicable')
    inventory['Stage latency'] = measured({p:distribution([r[p]['packing_seconds'] for r in results]) for p in ['before','after']},
        'seconds',24,'Local packing only','perf_counter; sequential, no model load or network; tokenizer first-load may affect initial sample','mean and p50/p95 diagnostics only')
    write(output / 'comparison.json', dict(baseline_commit='9a3c20f', rows=results, aggregate=aggregate, metric_inventory=inventory,
        frozen_hashes={str(p):sha256(p.read_bytes()).hexdigest() for p in [LIVE/'index-snapshot.json',LIVE/'frozen-cases.json',LIVE/'frozen-fact-labels.json',OLD/'financial-control-1/comparison.json']},
        method='A compatibility adapter omits the newly added reading field from baseline table serialization; both phases use identical original source, selected candidates, expanded parents and budgets. No historical artifact edited. Derived readings are not new source quotations.'))
    print(json.dumps(dict(aggregate=aggregate, contexts=[{k:r[k] for k in ['identity','group']} | {p: {k:r[p][k] for k in ['tokens','covered','audited_reading_cells']} for p in ['before','after']} for r in results]),indent=2))


if __name__ == '__main__':
    main()
