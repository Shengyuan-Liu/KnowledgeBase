"""Function-scoped storage and offline clients shared by backend tests."""

from unittest.mock import MagicMock, Mock

import chromadb
import pytest

from knowledgebase.api import app as api_module
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.storage.database import build_engine, build_session_factory, init_db
from knowledgebase.storage.vectordb import ChromaStore


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def engine(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'knowledgebase.db'}")
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def sessions(engine):
    init_db(engine)
    return build_session_factory(engine)


@pytest.fixture
def collection(tmp_path):
    return chromadb.PersistentClient(path=str(tmp_path / "chroma")).create_collection(
        name="test-chunks", embedding_function=None,
        configuration={"hnsw": {"space": "cosine"}},
    )


@pytest.fixture
def storage(sessions, collection):
    return sessions, ChromaStore(collection), collection


@pytest.fixture
def embeddings():
    client = Mock(spec=EmbeddingClient)
    client.embed_documents.side_effect = lambda texts: [[1.0, 0.0] for _ in texts]
    client.embed_query.return_value = [1.0, 0.0]
    return client


@pytest.fixture
def configured_app(tmp_path, monkeypatch, embeddings):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test-key")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    sdk = MagicMock()
    sdk.__enter__.return_value = sdk
    sdk_factory = Mock(return_value=sdk)
    monkeypatch.setattr(api_module, "OpenAI", sdk_factory)
    monkeypatch.setattr(api_module, "EmbeddingClient", Mock(return_value=embeddings))
    app = api_module.create_app()
    assert not (tmp_path / "data").exists()
    sdk_factory.assert_not_called()
    return app, embeddings, sdk
