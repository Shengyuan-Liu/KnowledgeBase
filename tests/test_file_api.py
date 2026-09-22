"""HTTP file workflows with real SQLite/Chroma and offline embeddings."""

from unittest.mock import Mock

from fastapi.testclient import TestClient
import pytest

from knowledgebase.api import app as api_module
from knowledgebase.rag.retrieval import retrieve
from knowledgebase.storage.operations import get_chunks, get_document_source, get_file


@pytest.fixture
def api(configured_app):
    app, embeddings, sdk = configured_app
    with TestClient(app) as client:
        yield client, app.state.resources, embeddings
    sdk.__exit__.assert_called_once()


def upload(client, text=b"The library closes at 5 PM.", name="notes.txt"):
    return client.post("/api/files", files={"file": (name, text, "text/plain")})


def test_upload_list_retrieve_delete_preserves_other_file(api):
    client, resources, embeddings = api
    assert client.get("/api/files").json() == []
    text = "  The café closes at 5 PM.\r\n"
    response = upload(client, text.encode(), "Notes.TXT")
    assert response.status_code == 201
    first = response.json()
    assert first["status"] == "ready"
    assert first["file_name"] == "Notes.TXT"
    assert first["error_message"] is None
    assert first["created_at"]
    second = upload(client, b"Keep this file.", "Notes.TXT").json()
    assert second["file_id"] != first["file_id"]
    assert {f["file_id"] for f in client.get("/api/files").json()} == {first["file_id"], second["file_id"]}
    with resources.sessions() as session:
        assert get_chunks(session, first["file_id"])[0].text == text
        hits = retrieve("When does the library close?", session, embeddings, resources.store)
        assert {h.chunk.file_id for h in hits} == {first["file_id"], second["file_id"]}

    deleted = client.delete(f"/api/files/{first['file_id']}")
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert [f["file_id"] for f in client.get("/api/files").json()] == [second["file_id"]]
    with resources.sessions() as session:
        assert get_file(session, first["file_id"]) is None
        assert get_chunks(session, first["file_id"]) == []
        assert [h.chunk.file_id for h in retrieve("What remains?", session, embeddings, resources.store)] == [second["file_id"]]


@pytest.mark.parametrize("name, content, message", [
    ("notes.pdf", b"Text.", "Only .txt and .md files are supported."),
    ("notes.txt", b"\xff", "The file must be UTF-8 encoded."),
    ("notes.txt", b"", "The file must contain nonempty text."),
    ("notes.txt", b" \n\t", "The file must contain nonempty text."),
])
def test_invalid_upload_is_400_without_records_or_model_calls(api, name, content, message):
    client, resources, embeddings = api
    response = upload(client, content, name)
    assert response.status_code == 400
    assert response.json() == {"detail": message}
    assert client.get("/api/files").json() == []
    embeddings.embed_documents.assert_not_called()


def test_missing_multipart_file_is_422_and_unknown_delete_is_404(api):
    client, resources, embeddings = api
    assert client.post("/api/files").status_code == 422
    assert client.delete("/api/files/missing").status_code == 404
    embeddings.embed_documents.assert_not_called()


@pytest.mark.parametrize("error_type", [RuntimeError, ValueError])
def test_provider_failure_is_500_and_failed_record_can_be_deleted(api, error_type):
    client, resources, embeddings = api
    embeddings.embed_documents.side_effect = error_type("Embedding request failed.")
    response = upload(client)
    assert response.status_code == 500
    assert response.json()["detail"] == "File processing failed. Check the file list for its status."
    file = client.get("/api/files").json()[0]
    assert file["status"] == "failed"
    assert file["error_message"] == "Embedding request failed."
    assert client.delete(f"/api/files/{file['file_id']}").status_code == 204
    assert client.get("/api/files").json() == []


def test_processing_is_visible_and_cannot_be_deleted_during_upload(api):
    client, resources, embeddings = api

    def embed(texts):
        file = client.get("/api/files").json()[0]
        assert file["status"] == "processing"
        response = client.delete(f"/api/files/{file['file_id']}")
        assert response.status_code == 409
        return [[1.0, 0.0] for _ in texts]

    embeddings.embed_documents.side_effect = embed
    response = upload(client)
    assert response.status_code == 201
    assert response.json()["status"] == "ready"


@pytest.mark.parametrize("error_type", [RuntimeError, KeyError])
def test_delete_failure_is_500_and_retry_cleans_the_file(api, error_type):
    client, resources, embeddings = api
    file_id = upload(client).json()["file_id"]
    store = resources.store
    failing_store = Mock(wraps=store)
    failing_store.delete_by_file_id.side_effect = error_type("Deletion failed.")
    resources.store = failing_store
    response = client.delete(f"/api/files/{file_id}")
    assert response.status_code == 500
    assert "Retry deletion" in response.json()["detail"]
    assert client.get("/api/files").json()[0]["status"] == "failed"
    with resources.sessions() as session:
        assert retrieve("What is in the file?", session, embeddings, store) == []
    resources.store = store
    assert client.delete(f"/api/files/{file_id}").status_code == 204
    assert client.get("/api/files").json() == []
    assert client.delete(f"/api/files/{file_id}").status_code == 404


def test_restart_reuses_data_and_openapi_describes_file_contract(configured_app):
    app, embeddings, sdk = configured_app
    with TestClient(app) as client:
        file = upload(client).json()
        schema = client.get("/openapi.json").json()
        assert schema["paths"]["/api/files"]["post"]["responses"]["201"]
        assert "multipart/form-data" in schema["paths"]["/api/files"]["post"]["requestBody"]["content"]
        assert schema["paths"]["/api/files/{file_id}"]["delete"]["responses"]["204"]
    sdk.__exit__.assert_called_once()
    with TestClient(api_module.create_app()) as client:
        assert client.get("/api/files").json() == [file]
        assert client.delete(f"/api/files/{file['file_id']}").status_code == 204
    assert sdk.__exit__.call_count == 2
    embeddings.embed_documents.assert_called_once()


def test_markdown_upload_chat_restart_and_delete_preserves_original_evidence(configured_app):
    app, embeddings, sdk = configured_app
    text = "# Library\r\n\r\nThe library closes at 5 PM.\r\n"
    sdk.responses.create.return_value = Mock(output_text="The library closes at 5 PM. [1]")
    with TestClient(app) as client:
        response = upload(client, text.encode(), "Hours.MD")
        assert response.status_code == 201
        file_id = response.json()["file_id"]
        result = client.post("/api/chat", json={"question": "When does the library close?"})
        assert result.status_code == 200
        answer = result.json()
        assert answer["sources"][0]["text"] == text
        conversation_id = answer["conversation_id"]

    with TestClient(api_module.create_app()) as client:
        resources = client.app.state.resources
        with resources.sessions() as session:
            assert get_document_source(session, file_id).text == text
            chunks = get_chunks(session, file_id)
            assert chunks[0].heading_path == ["Library"]
        assert client.get("/api/files").json()[0]["status"] == "ready"
        assert client.delete(f"/api/files/{file_id}").status_code == 204
        history = client.get(f"/api/conversations/{conversation_id}").json()
        assert history["messages"][-1]["sources"][0]["text"] == text
        assert history["messages"][-1]["sources"][0]["file_deleted"] is True
        with resources.sessions() as session:
            assert get_document_source(session, file_id) is None
            assert get_chunks(session, file_id) == []
    embeddings.embed_documents.assert_called_once_with([text])


def test_built_workspace_and_api_share_one_origin(configured_app, tmp_path):
    frontend = tmp_path / "built-ui"
    frontend.mkdir()
    (frontend / "index.html").write_text("<title>Knowledge Base</title>")
    with TestClient(api_module.create_app(frontend_dir=frontend)) as client:
        response = client.get("/")
        assert response.status_code == 200 and "Knowledge Base" in response.text
        assert response.headers["content-type"].startswith("text/html")
        assert client.get("/api/files").json() == []
        assert client.get("/api/unknown").status_code == 404
