"""Interrupted upload recovery using real SQLite and Chroma, without model calls."""

from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock

from fastapi.testclient import TestClient

from knowledgebase.api import app as api_module
from knowledgebase.rag.chunking import split_text
from knowledgebase.rag.retrieval import retrieve_evidence
from knowledgebase.services.files import FileService
from knowledgebase.storage.operations import create_file, get_chunks, get_file, save_chunks
from knowledgebase.storage.runtime import open_storage


def seed_partial(sessions, store, file_id="abandoned"):
    chunks = split_text("Unfinished indexing.", file_id)
    with sessions.begin() as session:
        create_file(session, file_id, "interrupted.txt")
        save_chunks(session, chunks)
    store.upsert_chunks(chunks, [[1.0, 0.0]])


def test_recovery_removes_partial_chunks_vectors_and_preserves_ready_files(storage, embeddings):
    sessions, store, collection = storage
    ready = FileService(sessions, store, embeddings=embeddings).ingest("ready.txt", b"Keep this evidence.")
    seed_partial(sessions, store)
    FileService(sessions, store).recover()
    FileService(sessions, store).recover()
    with sessions() as session:
        failed = get_file(session, "abandoned")
        assert failed.status == "failed" and "Re-upload" in failed.error_message
        assert get_chunks(session, "abandoned") == []
        assert get_file(session, ready).status == "ready"
        assert {r.chunk.file_id for r in retrieve_evidence("Evidence?", session, embeddings, store).chunks} == {ready}
    assert collection.get()["ids"] == [f"{ready}:child:0"]
    FileService(sessions, store).delete("abandoned")
    with sessions() as session:
        assert get_file(session, "abandoned") is None


def test_recovery_cleanup_failure_remains_ineligible_and_deletable(storage, embeddings):
    sessions, store, collection = storage
    seed_partial(sessions, store)
    broken = Mock(wraps=store)
    broken.delete_by_file_id.side_effect = RuntimeError("Cleanup unavailable.")
    FileService(sessions, broken).recover()
    with sessions() as session:
        assert "Cleanup pending" in get_file(session, "abandoned").error_message
        assert retrieve_evidence("Unfinished?", session, embeddings, store).chunks == []
    FileService(sessions, store).delete("abandoned")
    assert collection.count() == 0


def test_api_restart_recovers_abandoned_upload_and_allows_delete(configured_app):
    app, _, _ = configured_app
    with TestClient(app):
        seed_partial(app.state.resources.sessions, app.state.resources.store)
    with TestClient(api_module.create_app()) as client:
        file = client.get("/api/files").json()[0]
        assert file["status"] == "failed"
        assert client.delete(f"/api/files/{file['file_id']}").status_code == 204


def test_live_owner_cannot_be_recovered_by_a_second_process(tmp_path):
    root = Path(__file__).resolve().parents[1]
    child = "from pathlib import Path; import sys; from knowledgebase.storage.runtime import open_storage; " \
            "ctx=open_storage(Path(sys.argv[1])); ctx.__enter__()"
    with open_storage(tmp_path) as (sessions, store):
        seed_partial(sessions, store)
        result = subprocess.run([sys.executable, "-c", child, str(tmp_path)], cwd=root, capture_output=True, text=True)
        assert result.returncode != 0 and "already in use" in result.stderr
        with sessions() as session:
            assert get_file(session, "abandoned").status == "processing"
    with open_storage(tmp_path) as (sessions, _):
        with sessions() as session:
            assert get_file(session, "abandoned").status == "failed"


def test_process_exit_releases_ownership_and_next_open_recovers(tmp_path):
    root = Path(__file__).resolve().parents[1]
    code = """
import os, sys
from pathlib import Path
from knowledgebase.storage.runtime import open_storage
from knowledgebase.storage.operations import create_file
with open_storage(Path(sys.argv[1])) as (sessions, store):
    with sessions.begin() as session:
        create_file(session, 'crashed', 'crashed.txt')
    os._exit(7)
"""
    result = subprocess.run([sys.executable, "-c", code, str(tmp_path)], cwd=root, capture_output=True, text=True)
    assert result.returncode == 7
    with open_storage(tmp_path) as (sessions, _):
        with sessions() as session:
            assert get_file(session, "crashed").status == "failed"
