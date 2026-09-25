"""Isolated real HTTP/storage server for frontend browser tests; no model calls."""

from contextlib import asynccontextmanager
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

import anyio

from knowledgebase.config import Settings
from knowledgebase.api.app import create_app
from knowledgebase.api.dependencies import AppResources
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient, StreamingLLMClient
from knowledgebase.storage.runtime import open_storage
from knowledgebase.schemas import RelevanceScore


async def stream_fixture(messages):
    """Keep the cancellation fixture open until the browser disconnects."""
    yield "The library "
    if messages[0]["content"].startswith("Question:\nStop this question\n"):
        await anyio.sleep_forever()
    await anyio.sleep(0.4)
    yield "closes at 5 PM. "
    await anyio.sleep(0.4)
    yield "[1]"


@asynccontextmanager
async def lifespan(app):
    with TemporaryDirectory(prefix="knowledgebase-browser-") as directory:
        with open_storage(Path(directory)) as (sessions, store):
            embeddings = Mock(spec=EmbeddingClient)
            embeddings.embed_documents.side_effect = lambda texts: [[1.0, 0.0] for _ in texts]
            embeddings.embed_query.return_value = [1.0, 0.0]
            llm = Mock(spec=LLMClient)
            llm.generate.side_effect = lambda messages: json.loads(messages[-1]["content"])["question"]
            streaming_llm = Mock(spec=StreamingLLMClient)
            streaming_llm.stream.side_effect = stream_fixture
            reranker = Mock(model="offline-reranker", model_revision="test-revision", device="cpu", max_pair_tokens=1024, batch_size=4)
            reranker.score.side_effect = lambda question, candidates: [
                RelevanceScore(chunk_id=c.chunk_id, score=3.25) for c in candidates
            ]
            app.state.resources = AppResources(
                settings=Settings(
                    _env_file=None, openai_api_key="offline-browser-test",
                    chunking_strategy="parent_child", chunk_max_tokens=16, rerank_enabled=True,
                ),
                sessions=sessions,
                store=store,
                embeddings=embeddings,
                llm=llm,
                streaming_llm=streaming_llm,
                reranker=reranker,
            )
            yield


app = create_app()
app.router.lifespan_context = lifespan
