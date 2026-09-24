"""Isolate packing changes using exactly the previously recorded BGE selections."""

import importlib.util
import json
from pathlib import Path

from evals.evaluate import retrieval_metrics
from knowledgebase.config import RetrievalOptions
from cost_order_packing import pack_evidence
from knowledgebase.schemas import ChildChunk, StructuredChunk, RetrievedChunk, RetrievalDiagnostics

ROOT = Path(__file__).parent
PREVIOUS = ROOT.parent / '20260924T002009Z-bge-serialized'


def inputs(row, files):
    children = {c['chunk_id']: ChildChunk.model_validate(c) for f in files for c in f['chunks']}
    parents = {p['parent_id']: p for f in files for p in f['parents']}
    names = {f['file']['file_id']: f['file']['file_name'] for f in files}
    selected, expanded = [], {}
    for candidate in row['answer']['retrieval']['candidates']:
        chunk = children[candidate['chunk_id']]
        hit = RetrievedChunk(chunk=chunk, file_name=names[chunk.file_id],
                             distance=candidate['distance'], fusion=candidate['fusion'], rerank=candidate['rerank'],
                             parent_id=chunk.parent_id, matched_child_ids=[chunk.chunk_id])
        selected.append(hit)
        if chunk.parent_id not in expanded:
            parent = parents[chunk.parent_id]
            expanded[chunk.parent_id] = hit.model_copy(update={
                'chunk': StructuredChunk(chunk_id=chunk.parent_id, **{k: v for k, v in parent.items() if k != 'parent_id'}),
                'matched_child_ids': [],
            })
        expanded[chunk.parent_id].matched_child_ids.append(chunk.chunk_id)
    return selected, list(expanded.values())


def sources(evidence):
    return [{**item.chunk.model_dump(), 'source_id': index, 'file_name': item.file_name,
             'parent_id': item.parent_id, 'matched_child_ids': item.matched_child_ids,
             'distance': item.distance, 'fusion': item.fusion.model_dump(), 'rerank': item.rerank.model_dump()}
            for index, item in enumerate(evidence.chunks, start=1)]


def run():
    spec = importlib.util.spec_from_file_location('rank_order', ROOT / 'rank_order_packing.py')
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    cases = {c['id']: c for c in json.loads((ROOT / 'cases.json').read_text())}
    files = json.loads((ROOT / 'chunks.json').read_text())
    rows = [json.loads(line) for line in (PREVIOUS / 'answers.jsonl').read_text().splitlines()]
    with (ROOT / 'packing-replay.jsonl').open('x') as output:
        for row in rows:
            if row['strategy'] != 'bge':
                continue
            case = cases[row['case_id']]
            normalized = {**case, 'evidence': [{**span, 'file': Path(span['file']).name} for span in case['evidence']]}
            for strategy, packing, packer in [
                ('parent_first', 'parent_first', pack_evidence),
                ('child_first_rank_expansion', 'parent_then_child', original.pack_evidence),
                ('child_first_cost_expansion', 'parent_then_child', pack_evidence),
            ]:
                selected, expanded = inputs(row, files)
                diagnostics = RetrievalDiagnostics(
                    max_tokens=4096, tokenizer='cl100k_base', options=RetrievalOptions(packing_strategy=packing),
                )
                result = packer(selected, expanded, diagnostics)
                packed = sources(result)
                if strategy == 'parent_first':
                    assert [(s['chunk_id'], s['text']) for s in packed] == [(s['chunk_id'], s['text']) for s in row['answer']['sources']]
                record = {'case_id': case['id'], 'question': case['question'], 'strategy': strategy,
                          'frozen_selected_ids': [c.chunk.chunk_id for c in selected], 'sources': packed,
                          'diagnostics': result.diagnostics.model_dump(), 'coverage': retrieval_metrics(normalized, packed)}
                output.write(json.dumps(record) + '\n')
                print(case['id'], strategy, record['coverage']['annotated_char_recall'], flush=True)


if __name__ == '__main__':
    run()
