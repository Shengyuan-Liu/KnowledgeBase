"""Check the final whole-child retention policy against the same frozen inputs."""

import json
from pathlib import Path

from evals.evaluate import retrieval_metrics
from knowledgebase.config import RetrievalOptions
from knowledgebase.rag.packing import pack_evidence
from knowledgebase.schemas import RetrievalDiagnostics
from replay_packing import ROOT, PREVIOUS, inputs, sources


def run():
    cases = {c['id']: c for c in json.loads((ROOT / 'cases.json').read_text())}
    files = json.loads((ROOT / 'chunks.json').read_text())
    with (ROOT / 'parent-then-child-replay.jsonl').open('x') as output:
        for line in (PREVIOUS / 'answers.jsonl').read_text().splitlines():
            row = json.loads(line)
            if row['strategy'] != 'bge':
                continue
            selected, expanded = inputs(row, files)
            result = pack_evidence(selected, expanded, RetrievalDiagnostics(
                max_tokens=4096, tokenizer='cl100k_base', options=RetrievalOptions(packing_strategy='parent_then_child'),
            ))
            packed = sources(result)
            old_ids = {s['chunk_id'] for s in row['answer']['sources']}
            assert old_ids <= {s['chunk_id'] for s in packed}
            case = cases[row['case_id']]
            normalized = {**case, 'evidence': [{**span, 'file': Path(span['file']).name} for span in case['evidence']]}
            record = {'case_id': case['id'], 'question': case['question'], 'strategy': 'parent_then_child',
                      'frozen_selected_ids': [c.chunk.chunk_id for c in selected], 'sources': packed,
                      'diagnostics': result.diagnostics.model_dump(), 'coverage': retrieval_metrics(normalized, packed)}
            output.write(json.dumps(record) + '\n')
            print(case['id'], row['coverage']['annotated_char_recall'], record['coverage']['annotated_char_recall'], flush=True)


if __name__ == '__main__':
    run()
