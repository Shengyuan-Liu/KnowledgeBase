"""Replay the real financial selected hits through the production packing path."""

from knowledgebase.rag.retrieval import Retriever
import json
from pathlib import Path

import pytest
import tiktoken

from knowledgebase.rag.context import build_context
from knowledgebase.schemas import (
    File, RetrievedChunk, RetrievalDiagnostics, ChunkBatch, Chunk,
)

from knowledgebase.storage.operations import create_file, save_pdf_source, save_parent_child_chunks

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'evals/check-runs/20260927-pdf-evidence-packing'
LIVE = ROOT / 'evals/library-runs/20260927-v2-pdf-live'
FINANCIAL = {'apple-sales', 'apple-income', 'apparent-conflict'}


@pytest.fixture(scope='module')
def financial_inputs():
    snapshot=json.loads((LIVE/'index-snapshot.json').read_text())
    document=next(d for d in snapshot['files'] if d['file']['file_name']=='apple-fy24.pdf')
    rows=json.loads((RUN/'frozen-inputs.json').read_text())['rows']
    return document,{(r['case_id'],r['arm']):r for r in rows if r['case_id'] in FINANCIAL}


@pytest.mark.parametrize('case_id',sorted(FINANCIAL))
@pytest.mark.parametrize('arm',['single','planned'])
def test_financial_hits_keep_values_periods_units_and_exact_budget(sessions, financial_inputs, case_id, arm):
    document,rows=financial_inputs
    row=rows[(case_id,arm)]
    extraction=File.model_validate({"type": "pdf", **document['extraction']})
    identity=document['file']['file_id']
    children={c['chunk_id']:Chunk.model_validate({**c, "type": "child"}) for c in document['chunks']}
    with sessions.begin() as session:
        create_file(session,identity,'apple-fy24.pdf')
        save_pdf_source(session,identity,extraction,indexing={})
        save_parent_child_chunks(session,ChunkBatch(
            parents=[Chunk.model_validate({**c, "chunk_id": c["parent_id"], "parent_id": None, "type": "parent"}) for c in document['parents']],children=list(children.values())))
    selected=[RetrievedChunk.model_validate({**hit,'chunk':children[hit['chunk']['chunk_id']]}) for hit in row['selected']]
    with sessions() as session:
        result=Retriever.pack(selected, session, RetrievalDiagnostics.model_validate(row['diagnostics']))
    context=build_context(result.chunks)
    expected=['14,736','93,736'] if case_id=='apple-income' else ['94,930','391,035']
    assert all(value in context for value in [*expected,'Three Months Ended','Twelve Months Ended','September 28, 2024','In millions'])
    first = result.chunks[0]
    assert first.chunk.file_id == selected[0].chunk.file_id
    assert first.chunk.start_offset <= selected[0].chunk.start_offset < selected[0].chunk.end_offset <= first.chunk.end_offset
    assert len(tiktoken.get_encoding('cl100k_base').encode_ordinary(context)) == result.diagnostics.evidence_tokens <= 4096
    for hit in result.chunks:
        assert hit.chunk.text == extraction.text[hit.chunk.start_offset:hit.chunk.end_offset]
        assert all(extra.text==extraction.text[extra.start_offset:extra.end_offset] for extra in hit.pdf.supplements)
        if hit.chunk.chunk_id != hit.parent_id:
            assert hit.parent_id not in {other.chunk.chunk_id for other in result.chunks}
    units=[extra for hit in result.chunks for extra in hit.pdf.supplements if extra.role=='preceding_text']
    assert (any('In millions' in extra.text and {r.page_index for r in extra.regions}=={0} for extra in units)
            or any('In millions' in hit.chunk.text and 0 in {r.page_index for r in hit.pdf.regions}
                   for hit in result.chunks))
