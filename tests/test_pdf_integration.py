"""PDF ingestion/lifecycle with frozen real extraction and offline providers."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from knowledgebase.api import app as api_module
from knowledgebase.rag.context import build_context
from knowledgebase.rag.chunking import split_parent_child
from knowledgebase.rag.pdf_models import PdfExtraction
from knowledgebase.rag.pdf_evidence import pdf_evidence, table_rows
from knowledgebase.schemas import RetrievedChunk, RetrievalDiagnostics, RetrievalOptions
from knowledgebase.rag.packing import pack_evidence
from knowledgebase.rag.retrieval import retrieve
from knowledgebase.services.files import ingest_file, delete_file, recover_interrupted_files
from knowledgebase.storage.operations import (
    create_file, get_file, get_document_source, get_pdf_extraction, get_chunks,
    save_pdf_source, update_file_status,
)
from knowledgebase.storage.pdf_assets import PdfAssets
from knowledgebase.storage.database import init_db

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "evals/materials/pdf-v2/apple-fy24.pdf"
EXTRACTION = ROOT / "evals/check-runs/20260926-pdf-parser-selection/adapter-2/apple-fy24.json"


@pytest.fixture
def extraction():
    return PdfExtraction.model_validate_json(EXTRACTION.read_text())


@pytest.fixture
def pdf_api(configured_app, extraction):
    app, embeddings, sdk = configured_app
    sdk.responses.create.return_value = Mock(output_text="Quarterly net sales were 94,930 million. [1]")
    with TestClient(app) as client:
        app.state.resources.pdf_parser = Mock(parse=Mock(return_value=extraction))
        yield client, app.state.resources, embeddings


def upload_pdf(client):
    response = client.post("/api/files", files={"file": ("Report.PDF", PDF.read_bytes(), "application/pdf")})
    assert response.status_code == 201, response.text
    return response.json()


def test_upload_query_original_range_and_historical_evidence(pdf_api, extraction):
    client, resources, _ = pdf_api
    file = upload_pdf(client)
    assert file["page_count"] == 4 and file["extraction_warnings"]
    file_id = file["file_id"]
    with resources.sessions() as session:
        source = get_document_source(session, file_id)
        assert source.source_format == "pdf"
        assert get_pdf_extraction(session, file_id) == extraction
        assert all(c.text == source.text[c.start_offset:c.end_offset] for c in get_chunks(session, file_id))
    url = f"/api/files/{file_id}/original?revision={extraction.revision_id}"
    original = client.get(url)
    assert original.content == PDF.read_bytes()
    assert original.headers["content-type"] == "application/pdf"
    assert original.headers["cache-control"] == "no-store"
    assert "inline" in original.headers["content-disposition"]
    assert client.get(url, headers={"Range": "bytes=0-15"}).content == PDF.read_bytes()[:16]
    assert client.get(f"/api/files/{file_id}/original?revision=old").status_code == 409
    answer = client.post("/api/chat", json={"question": "What were total net sales?", "file_ids": [file_id]}).json()
    assert answer["sources"]
    for source in answer["sources"]:
        assert source["pdf"]["revision_id"] == extraction.revision_id
        assert source["pdf"]["regions"]
        assert source["start_line"] is None
        for extra in source["pdf"]["supplements"]:
            assert extra["text"] == extraction.text[extra["start_offset"]:extra["end_offset"]]
    assert client.delete(f"/api/files/{file_id}").status_code == 204
    assert not resources.assets.path(file_id).exists()
    assert client.get(url).status_code == 404
    history = client.get(f"/api/conversations/{answer['conversation_id']}").json()
    saved = history["messages"][-1]["sources"]
    assert [s["pdf"] for s in saved] == [s["pdf"] for s in answer["sources"]]
    assert all(s["file_deleted"] for s in saved)
    with resources.sessions() as session:
        assert get_pdf_extraction(session, file_id) is None
        assert retrieve("net sales", session, resources.embeddings, resources.store) == []


def test_streaming_and_history_share_pdf_provenance(pdf_api):
    client, resources, _ = pdf_api
    file = upload_pdf(client)
    async def stream(_messages):
        yield "Net sales were 94,930 million. [1]"
    resources.streaming_llm.stream = stream
    result = client.post("/api/chat/stream", json={"question": "Net sales?", "request_id": "pdf-stream", "file_ids": [file["file_id"]]})
    import json
    assert result.status_code == 200, result.text
    events = []
    for frame in result.text.strip().split("\n\n"):
        event, data = frame.split("\n")
        events.append({"event": event.removeprefix("event: "), **json.loads(data.removeprefix("data: "))})
    sources = next(e["sources"] for e in events if e["event"] == "sources")
    complete = next(e for e in events if e["event"] == "complete")
    assert sources == complete["sources"]
    history = client.get(f"/api/conversations/{complete['conversation_id']}").json()
    assert [s["pdf"] for s in history["messages"][-1]["sources"]] == [s["pdf"] for s in sources]


def test_invalid_or_scanned_pdf_does_not_embed_and_cleans_assets(pdf_api, extraction):
    client, resources, embeddings = pdf_api
    response = client.post("/api/files", files={"file": ("bad.pdf", b"not pdf", "application/pdf")})
    assert response.status_code == 400
    assert client.get("/api/files").json() == []
    resources.pdf_parser.parse.return_value = extraction.model_copy(update={"text": "", "blocks": ()})
    response = client.post("/api/files", files={"file": ("scan.pdf", b"%PDF-1.7", "application/pdf")})
    assert response.status_code == 400 and "OCR is disabled" in response.text
    failed = client.get("/api/files").json()[0]
    assert failed["status"] == "failed"
    assert not resources.assets.path(failed["file_id"]).exists()
    embeddings.embed_documents.assert_not_called()


def test_provider_failure_and_failed_cleanup_can_be_deleted(pdf_api):
    client, resources, embeddings = pdf_api
    embeddings.embed_documents.side_effect = RuntimeError("offline embedding failure")
    original_assets = resources.assets
    resources.assets = Mock(wraps=original_assets)
    resources.assets.delete.side_effect = OSError("asset cleanup failed")
    response = client.post("/api/files", files={"file": ("bad.pdf", PDF.read_bytes(), "application/pdf")})
    assert response.status_code == 500
    failed = client.get("/api/files").json()[0]
    assert "Cleanup pending" in failed["error_message"]
    assert original_assets.path(failed["file_id"]).exists()
    assert client.get(f"/api/files/{failed['file_id']}/original").status_code == 404
    resources.assets = original_assets
    assert client.delete(f"/api/files/{failed['file_id']}").status_code == 204
    assert not original_assets.path(failed["file_id"]).exists()


def test_restart_keeps_pdf_and_recovers_interrupted_assets(configured_app, extraction):
    app, _, _ = configured_app
    with TestClient(app) as client:
        resources = app.state.resources
        resources.pdf_parser = Mock(parse=Mock(return_value=extraction))
        file = upload_pdf(client)
        with resources.sessions.begin() as session:
            create_file(session, "interrupted", "unfinished.pdf")
            save_pdf_source(session, "interrupted", extraction, {})
        resources.assets.save("interrupted", PDF.read_bytes())
    with TestClient(api_module.create_app()) as client:
        resources = client.app.state.resources
        files = {f["file_id"]: f for f in client.get("/api/files").json()}
        assert files[file["file_id"]]["status"] == "ready"
        assert client.get(f"/api/files/{file['file_id']}/original").content == PDF.read_bytes()
        assert files["interrupted"]["status"] == "failed"
        assert not resources.assets.path("interrupted").exists()
        with resources.sessions() as session:
            assert get_pdf_extraction(session, "interrupted") is None


def test_asset_delete_failure_is_ineligible_until_retry(pdf_api):
    client, resources, _ = pdf_api
    file = upload_pdf(client)
    assets = resources.assets
    resources.assets = Mock(wraps=assets)
    resources.assets.delete.side_effect = OSError("permission failure")
    assert client.delete(f"/api/files/{file['file_id']}").status_code == 500
    with resources.sessions() as session:
        assert get_file(session, file["file_id"]).status == "failed"
        assert retrieve("net sales", session, resources.embeddings, resources.store) == []
    resources.assets = assets
    assert client.delete(f"/api/files/{file['file_id']}").status_code == 204
    assert not assets.path(file["file_id"]).exists()


def test_additive_schema_keeps_existing_txt_constraints_and_data(engine, sessions, extraction):
    # Recreate a genuine pre-v2 schema without the new table, then run init_db.
    from knowledgebase.storage.models import PdfSourceRecord
    with engine.begin() as connection:
        PdfSourceRecord.__table__.drop(connection)
    with sessions.begin() as session:
        create_file(session, "legacy", "legacy.txt")
    init_db(engine)
    assert "pdf_sources" in inspect(engine).get_table_names()
    constraints = inspect(engine).get_check_constraints("document_sources")
    assert any("'txt', 'md'" in c["sqltext"] for c in constraints)
    with sessions() as session:
        assert get_file(session, "legacy").file_name == "legacy.txt"


def test_split_table_headers_are_separately_located_and_budgeted(extraction):
    hierarchy = split_parent_child(extraction.text, extraction.source_blocks(), "file",
        parent_max_tokens=96, child_max_tokens=48, encoding_name="cl100k_base", table_row_spans=table_rows(extraction))
    chunk = next(c for c in hierarchy.children if "94,930" in c.text)
    item = RetrievedChunk(chunk=chunk, file_name="report.pdf", distance=0,
                          pdf=pdf_evidence(extraction, chunk.start_offset, chunk.end_offset))
    assert item.pdf.supplements
    assert any("Three Months Ended" in e.text for e in item.pdf.supplements)
    assert all(e.text == extraction.text[e.start_offset:e.end_offset] for e in item.pdf.supplements)
    import tiktoken
    tokens = len(tiktoken.get_encoding("cl100k_base").encode_ordinary(build_context([item])))
    assert tokens > chunk.token_count
    diagnostics = RetrievalDiagnostics(max_tokens=tokens-1, tokenizer="cl100k_base", options=RetrievalOptions())
    assert pack_evidence([item], [item], diagnostics).chunks == []
    diagnostics = RetrievalDiagnostics(max_tokens=tokens, tokenizer="cl100k_base", options=RetrievalOptions())
    packed = pack_evidence([item], [item], diagnostics)
    assert packed.chunks == [item] and packed.diagnostics.evidence_tokens == tokens


def test_pdf_rows_fit_whole_when_budget_allows(extraction):
    hierarchy = split_parent_child(extraction.text, extraction.source_blocks(), "file",
        parent_max_tokens=120, child_max_tokens=60, encoding_name="cl100k_base", table_row_spans=table_rows(extraction))
    import tiktoken
    encoding = tiktoken.get_encoding("cl100k_base")
    for rows in table_rows(extraction).values():
        for start, end in rows:
            if start < end and len(encoding.encode_ordinary(extraction.text[start:end])) <= 60:
                assert any(c.start_offset <= start and end <= c.end_offset for c in hierarchy.children)
