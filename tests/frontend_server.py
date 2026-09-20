"""Isolated real HTTP/storage server for frontend browser tests; no model calls."""

from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from knowledgebase.api.app import create_app
from knowledgebase.api.dependencies import AppResources
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient, StreamingLLMClient
from knowledgebase.storage.runtime import open_storage


@asynccontextmanager
async def lifespan(app):
    with TemporaryDirectory(prefix="knowledgebase-browser-") as directory:
        with open_storage(Path(directory)) as (sessions, store):
            embeddings = Mock(spec=EmbeddingClient)
            embeddings.embed_documents.side_effect = lambda texts: [[1.0, 0.0] for _ in texts]
            app.state.resources = AppResources(
                sessions=sessions,
                store=store,
                embeddings=embeddings,
                llm=Mock(spec=LLMClient),
                streaming_llm=Mock(spec=StreamingLLMClient),
            )
            yield


app = create_app()
app.router.lifespan_context = lifespan
