"""Regressions for the real page-62 title/body separation and its PDF boundaries."""

from dataclasses import asdict

import json
from pathlib import Path
from unittest.mock import Mock

import pytest
import tiktoken

from knowledgebase.config import RetrievalOptions
from knowledgebase.rag.chunking import split_parent_child
from knowledgebase.rag.context import build_context
from knowledgebase.rag.pdf_chunking import PDF_PARENT_CONTEXT_VERSION, join_heading_parents
from knowledgebase.rag.pdf_evidence import table_rows
from knowledgebase.schemas import (
    File, Chunk, ChunkBatch, RetrievedChunk, RetrievalDiagnostics,
)
from knowledgebase.rag.retrieval import pack_retrieval_candidates
from knowledgebase.services.files import DocumentChunker, FileService
from knowledgebase.storage.operations import create_file, get_chunks, get_document_source, get_parents, save_parent_child_chunks, save_pdf_source
from knowledgebase.storage.pdf_assets import PdfAssets


ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / 'evals/library-runs/20260929-new-pdf-chain'
TITLE = 'NB with Bag of Words for text classification'
DOCUMENT_COUNT = 'Count how many documents you have from each topic'
WORD_COUNT = 'For each topic, count how many times you saw word'


@pytest.fixture(scope='module')
def documents():
    return {d['file']['file_name']: d for d in json.loads((LIVE / 'index-snapshot.json').read_text())['files']}


def records(document):
    return (File.model_validate({"type": "pdf", **document['extraction']}), ChunkBatch(
        parents=[Chunk.model_validate({**p, "chunk_id": p["parent_id"], "parent_id": None, "type": "parent"}) for p in document['parents']],
        children=[Chunk.model_validate({**c, "type": "child"}) for c in document['chunks']],
    ))


@pytest.mark.parametrize('name', ['ml-lecture.pdf', 'doclaynet.pdf', 'docling-report.pdf', 'apple-fy24.pdf', 'background-checks.pdf'])
def test_frozen_pdf_context_keeps_exact_children_source_regions_and_parent_budget(documents, name):
    extraction, original = records(documents[name])
    before = asdict(original)
    result = join_heading_parents(extraction, original)
    assert asdict(original) == before
    assert [c.model_dump(exclude={'parent_id'}) for c in result.children] == [c.model_dump(exclude={'parent_id'}) for c in original.children]
    assert result == join_heading_parents(extraction, original)
    parents = {p.chunk_id: p for p in result.parents}
    encoding = tiktoken.get_encoding('cl100k_base')
    end = 0
    for i, parent in enumerate(result.parents):
        assert parent.index == i and parent.chunk_id.endswith(f':parent:{i}')
        assert parent.text == extraction.text[parent.start_offset:parent.end_offset]
        assert not extraction.text[end:parent.start_offset].strip()
        assert parent.token_count == len(encoding.encode_ordinary(parent.text)) <= parent.max_tokens
        assert parent.source_block_indices == [i for i, b in enumerate(extraction.blocks)
                                                if b.start_offset < parent.end_offset and parent.start_offset < b.end_offset]
        end = parent.end_offset
    assert not extraction.text[end:].strip()
    for child in result.children:
        parent = parents[child.parent_id]
        assert parent.start_offset <= child.start_offset < child.end_offset <= parent.end_offset


def test_lecture_title_hit_supplies_both_count_bullets_with_original_page_citation(sessions, documents):
    document = documents['ml-lecture.pdf']
    extraction, original = records(document)
    merged = join_heading_parents(extraction, original)
    child = next(c for c in merged.children if c.text == TITLE)
    original_child = next(c for c in original.children if c.chunk_id == child.chunk_id)
    assert next(p for p in original.parents if p.chunk_id == original_child.parent_id).text == TITLE
    with sessions.begin() as session:
        create_file(session, child.file_id, 'ml-lecture.pdf')
        save_pdf_source(session, child.file_id, extraction, {})
        save_parent_child_chunks(session, merged)
    with sessions() as session:
        result = pack_retrieval_candidates([RetrievedChunk(chunk=child, file_name='ml-lecture.pdf',
            distance=0, parent_id=child.parent_id, matched_child_ids=[child.chunk_id])], session,
            RetrievalDiagnostics(max_tokens=4096, tokenizer='cl100k_base',
                                 options=RetrievalOptions(packing_strategy='parent_then_child')))
    context = build_context(result.chunks)
    assert DOCUMENT_COUNT in context and WORD_COUNT in context
    assert len(result.chunks) == 1
    supplied = result.chunks[0]
    assert {r.page_index for r in supplied.pdf.regions} == {61}
    assert supplied.pdf.revision_id == extraction.revision_id
    assert supplied.chunk.text == extraction.text[supplied.chunk.start_offset:supplied.chunk.end_offset]
    assert supplied.matched_child_ids == [child.chunk_id]
    assert result.diagnostics.evidence_tokens == len(tiktoken.get_encoding('cl100k_base').encode_ordinary(context)) <= 4096


def test_real_cross_page_title_and_footer_only_section_do_not_join(documents):
    for name, title in [('ml-lecture.pdf', 'Overfitting …'), ('background-checks.pdf', 'NOTES:')]:
        extraction, original = records(documents[name])
        result = join_heading_parents(extraction, original)
        child = next(c for c in result.children if c.text == title)
        assert next(p for p in result.parents if p.chunk_id == child.parent_id).text == title


def test_real_heading_body_pair_remains_separate_when_combined_parent_exceeds_budget(documents):
    extraction, _ = records(documents['ml-lecture.pdf'])
    original = split_parent_child(extraction.text, extraction.blocks, 'file',
        parent_max_tokens=64, child_max_tokens=32, encoding_name='cl100k_base', table_row_spans=table_rows(extraction))
    result = join_heading_parents(extraction, original)
    title = next(c for c in result.children if c.text == TITLE)
    count = next(c for c in result.children if DOCUMENT_COUNT in c.text)
    assert title.parent_id != count.parent_id
    assert all(p.token_count <= 64 for p in result.parents)


def test_pdf_ingestion_persists_joined_parents_and_embeds_original_children(sessions, tmp_path, documents):
    extraction, _ = records(documents['ml-lecture.pdf'])
    embeddings = Mock()
    embeddings.embed_documents.side_effect = lambda texts: [[1.0] for _ in texts]
    store = Mock()
    file_id = FileService(sessions, store, embeddings=embeddings, assets=PdfAssets(tmp_path), pdf_parser=Mock(parse=Mock(return_value=extraction)), chunker=DocumentChunker(parent_max_tokens=1536, chunk_max_tokens=512)).ingest('ml-lecture.pdf', (ROOT / 'evals/materials/pdf-v2/ml-lecture.pdf').read_bytes())
    baseline = split_parent_child(extraction.text, extraction.blocks, file_id,
        parent_max_tokens=1536, child_max_tokens=512, encoding_name='cl100k_base', table_row_spans=table_rows(extraction))
    assert embeddings.embed_documents.call_args.args[0] == [c.text for c in baseline.children]
    with sessions() as session:
        children = get_chunks(session, file_id)
        parents = {p.chunk_id: p for p in get_parents(session, file_id)}
        source = get_document_source(session, file_id)
    title = next(c for c in children if c.text == TITLE)
    assert DOCUMENT_COUNT in parents[title.parent_id].text and WORD_COUNT in parents[title.parent_id].text
    assert source.indexing['pdf_parent_context'] == PDF_PARENT_CONTEXT_VERSION
    assert source.text == extraction.text
