"""Compare parent context with frozen selections; never call a model or change a library."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
from statistics import mean
from time import perf_counter

import tiktoken

from knowledgebase.rag.context import build_context
from knowledgebase.rag.pdf_chunking import join_heading_parents
from knowledgebase.rag.pdf_models import PdfExtraction
from knowledgebase.rag.retrieval import pack_retrieval_candidates
from knowledgebase.schemas import ChildChunk, ParentChildChunks, ParentChunk, RetrievedChunk, RetrievalDiagnostics
from knowledgebase.storage.database import build_engine, build_session_factory, init_db
from knowledgebase.storage.operations import create_file, save_parent_child_chunks, save_pdf_source
from record_check import METRICS

ROOT = Path(__file__).resolve().parent
LIVE = Path('evals/library-runs/20260929-new-pdf-chain')


def write(name, value):
    with (ROOT / name).open('x') as file:
        file.write(json.dumps(value, indent=2) + '\n')


def covered(result, label):
    return all(any(hit.chunk.file_id == span['file_id']
                   and hit.chunk.start_offset <= span['start'] and span['end'] <= hit.chunk.end_offset
                   and anchor['anchor'].casefold() in hit.chunk.text.casefold()
                   for hit in result.chunks for span in anchor['spans']) for anchor in label['anchors'])


def distribution(values):
    values = sorted(values)
    def percentile(p):
        position = (len(values)-1)*p
        low = int(position)
        return values[low] + (values[min(low+1,len(values)-1)]-values[low])*(position-low)
    return dict(n=len(values), mean=mean(values), p50=percentile(.5), p95=percentile(.95),
                unit='seconds', percentile_method='linear interpolation')


def replay():
    frozen = json.loads((ROOT / 'frozen-inputs.json').read_text())
    assert all(sha256(Path(p).read_bytes()).hexdigest() == digest for p, digest in frozen['files'].items())
    snapshot = json.loads((LIVE / 'index-snapshot.json').read_text())
    cases = json.loads((LIVE / 'frozen-cases.json').read_text())['cases']
    labels = json.loads((LIVE / 'frozen-labels.json').read_text())
    old_diagnostics = json.loads((LIVE / 'diagnostics.json').read_text())
    encoding = tiktoken.get_encoding('cl100k_base')
    rows, corpus = [], []
    for phase in ['before', 'after']:
        engine = build_engine('sqlite://')
        init_db(engine)
        sessions = build_session_factory(engine)
        children, extractions = {}, {}
        with sessions.begin() as session:
            for document in snapshot['files']:
                extraction = PdfExtraction.model_validate(document['extraction'])
                identity = document['file']['file_id']
                extractions[identity] = extraction
                hierarchy = ParentChildChunks(parents=[ParentChunk.model_validate(p) for p in document['parents']],
                                              children=[ChildChunk.model_validate(c) for c in document['chunks']])
                original = hierarchy
                started = perf_counter()
                if phase == 'after':
                    hierarchy = join_heading_parents(extraction, hierarchy)
                grouping_seconds = perf_counter()-started
                assert [c.model_dump(exclude={'parent_id'}) for c in hierarchy.children] == [c.model_dump(exclude={'parent_id'}) for c in original.children]
                corpus.append(dict(phase=phase, file=document['file']['file_name'], parents=len(hierarchy.parents),
                                   children=len(hierarchy.children), grouping_seconds=grouping_seconds,
                                   child_content_ids_offsets_headings_unchanged=True,
                                   parent_links_changed=sum(c.parent_id != p.parent_id for c, p in zip(hierarchy.children, original.children, strict=True))))
                children.update({c.chunk_id: c for c in hierarchy.children})
                create_file(session, identity, document['file']['file_name'])
                save_pdf_source(session, identity, extraction, {})
                save_parent_child_chunks(session, hierarchy)
        for case in cases:
            answer = json.loads((LIVE / (case['id'] + '-planned.json')).read_text())
            planning = answer['answer']['retrieval']['planning']
            trace = planning['trace']
            selected = []
            merged = {candidate['chunk_id']: candidate for candidate in trace['merged']}
            for identity in trace['selected_ids']:
                vote = min(merged[identity]['votes'], key=lambda v: (v['rank'], v['run_index']))
                hit = next(h for h in trace['runs'][vote['run_index']]['result']['hits'] if h['chunk']['chunk_id'] == identity)
                child = children[identity]
                selected.append(RetrievedChunk.model_validate({**hit, 'chunk': child, 'parent_id': child.parent_id}))
            diagnostics = RetrievalDiagnostics.model_validate({**answer['answer']['retrieval'], 'planning': None})
            # Candidate metadata must describe the current parent associations, too.
            for candidate in diagnostics.candidates:
                candidate.parent_id = children[candidate.chunk_id].parent_id
            started = perf_counter()
            with sessions() as session:
                result = pack_retrieval_candidates(selected, session, diagnostics)
            seconds = perf_counter()-started
            context = build_context(result.chunks)
            assert result.diagnostics.evidence_tokens == len(encoding.encode_ordinary(context)) <= 4096
            if phase == 'before':
                assert context == planning['assessment']['context'], f'Baseline replay drift: {case["id"]}'
            for hit in result.chunks:
                extraction = extractions[hit.chunk.file_id]
                assert hit.chunk.text == extraction.text[hit.chunk.start_offset:hit.chunk.end_offset]
                assert tuple(hit.pdf.regions) == extraction.locate(hit.chunk.start_offset, hit.chunk.end_offset)
                assert all(s.text == extraction.text[s.start_offset:s.end_offset] for s in hit.pdf.supplements)
            rows.append(dict(phase=phase, case_id=case['id'], question=case['question'], selected_ids=trace['selected_ids'],
                             context=context, result=result.model_dump(mode='json'), seconds=seconds,
                             coverage={f: covered(result, labels[f]) for f in case['expected_fact_ids']}))
        engine.dispose()
    before, after = rows[:len(cases)], rows[len(cases):]
    pairs = []
    for b, a in zip(before, after, strict=True):
        assert b['case_id'] == a['case_id'] and b['selected_ids'] == a['selected_ids']
        pairs.append(dict(case_id=b['case_id'], before=b['coverage'], after=a['coverage'],
                          improved=[f for f in a['coverage'] if a['coverage'][f] and not b['coverage'][f]],
                          regressed=[f for f in b['coverage'] if b['coverage'][f] and not a['coverage'][f]],
                          before_tokens=b['result']['diagnostics']['evidence_tokens'], after_tokens=a['result']['diagnostics']['evidence_tokens']))
    inventory = {m: dict(status='not_applicable', value=None, unit=None, sample_count=None,
                        population='Offline fixed-candidate context replay', method='Not exercised', aggregation='none',
                        artifact='replay-results.json', reason='No live retrieval, model inference, HTTP/SSE request, ingestion, lifecycle or load workload.') for m in METRICS}
    for metric in METRICS[:5]:
        inventory[metric] = dict(status='measured', value=dict(before=old_diagnostics['summary']['final_selected_macro'][metric],
                                                             after=old_diagnostics['summary']['final_selected_macro'][metric]),
            unit='ratio', sample_count=5, population='Same selected children for five answerable cases; one no-gold case excluded',
            method='K=5 frozen full-anchor binary child labels, unchanged child content/IDs/ranks. Child recall denominator is all labeled relevant children; precision denominator is 5. Ranking scores copied from frozen diagnostics because every scoring input is unchanged. Labels are non-exhaustive.',
            aggregation='Case macro mean', artifact='../../../library-runs/20260929-new-pdf-chain/diagnostics.json')
    def measured(name, value, unit, count, method, aggregation='per case'):
        inventory[name] = dict(status='measured', value=value, unit=unit, sample_count=count,
                               population='Matched offline six-case replay', method=method, aggregation=aggregation, artifact='replay-results.json')
    totals = {phase: dict(covered=sum(sum(row['coverage'].values()) for row in rows if row['phase'] == phase), expected=16) for phase in ['before','after']}
    measured('Final evidence coverage', totals, 'source-fact anchor groups', 16,
             'Every frozen anchor present inside exact supplied body text/ranges. Same source spans before/after; does not measure correctness of a generated answer.', 'micro count')
    measured('Stage latency', {phase: distribution([r['seconds'] for r in rows if r['phase'] == phase]) for phase in ['before','after']},
             'seconds', 12, 'perf_counter around SQL parent loading, PDF provenance attachment and packing; CPU only, tokenizer loaded before both arms. Excludes parsing, embedding, search, reranking, network and model/queue time; one observation per case/arm is not a speed benchmark.', 'n/mean/P50/P95')
    measured('Token usage and cost', dict(evidence_tokens=[dict(case_id=p['case_id'], before=p['before_tokens'], after=p['after_tokens']) for p in pairs],
                                        provider_usage=dict(status='not_applicable', value=None, reason='No provider calls.'),
                                        billed_cost=dict(status='not_applicable', value=None, reason='No paid workload.')),
             'cl100k_base context tokens', 12, 'Count the complete serialized evidence, including metadata and PDF table readings, under the unchanged 4096-token cap.')
    measured('Reliability', dict(completed=12, failed=0, retries=0, baseline_contexts_match=6), 'offline packing calls', 12,
             'Successful replay, exact source/provenance, unchanged selections and budget assertions; not network reliability.', 'counts')
    result = dict(at=datetime.now(timezone.utc).isoformat(), device=platform.platform(),
                  frozen_inputs_sha256=sha256((ROOT / 'frozen-inputs.json').read_bytes()).hexdigest(),
                  corpus=corpus, pairs=pairs, rows=rows, metric_inventory=inventory,
                  limits=['Same late-round plans and selected children replayed; changed context could change future live assessment/queries/rankings.',
                          'Reference facts and source bytes frozen; no new generated answers, answer-quality score or fresh candidate retrieval gain.',
                          'Stored libraries are unchanged; new parent grouping requires affected PDFs to be reindexed.'])
    write('replay-results.json', result)
    print('Supplied evidence coverage:', totals)
    print('Improvements:', [(p['case_id'], p['improved']) for p in pairs if p['improved']])
    print('Regressions:', [(p['case_id'], p['regressed']) for p in pairs if p['regressed']])
    print('Evidence token counts:', [(p['case_id'], p['before_tokens'], p['after_tokens']) for p in pairs])


if __name__ == '__main__':
    replay()
