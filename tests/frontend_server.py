"""Isolated real HTTP/storage server for frontend browser tests; no model calls."""

from contextlib import asynccontextmanager
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep
from types import SimpleNamespace
from unittest.mock import Mock

import anyio

from knowledgebase.config import Settings
from knowledgebase.api.app import create_app
from knowledgebase.api.dependencies import AppResources
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient, StreamingLLMClient
from knowledgebase.providers.planner import PlannerClient
from knowledgebase.config import PlanningOptions
from knowledgebase.storage.runtime import open_storage
from knowledgebase.storage.pdf_assets import PdfAssets
from knowledgebase.rag.pdf_models import PdfExtraction
from knowledgebase.schemas import RelevanceScore


async def stream_fixture(messages):
    """Keep the cancellation fixture open until the browser disconnects."""
    if "total net sales" in messages[0]["content"].lower():
        yield "Total net sales were 94,930 million. [1]"
        return
    yield "The library "
    if messages[0]["content"].startswith("Question:\nStop this question\n"):
        await anyio.sleep_forever()
    await anyio.sleep(0.4)
    yield "closes at 5 PM. "
    await anyio.sleep(0.4)
    yield "[1]"


def plan_fixture(**kwargs):
    question = json.loads(kwargs["input"][-1]["content"])["original_question"]
    sleep(2 if question.startswith("Stop planning") else 0.3)
    decision = {"route": "decomposed", "requirements": [
        {"requirement_id": "hours", "description": "Closing hours"},
        {"requirement_id": "access", "description": "Library access"},
    ], "queries": [
        {"query_id": "hours", "text": "library closing hours", "requirement_ids": ["hours"]},
        {"query_id": "access", "text": "library access", "requirement_ids": ["access"]},
    ]}
    return SimpleNamespace(status="completed", output_text=json.dumps(decision),
                           model="offline-planner", id="offline-plan", usage=None)


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
            for provider in (embeddings, llm, streaming_llm):
                provider.bounded.return_value = provider
            planner_sdk = Mock()
            planner_sdk.with_options.return_value = planner_sdk
            planner_sdk.responses.create.side_effect = plan_fixture
            reranker = Mock(model="offline-reranker", model_revision="test-revision", device="cpu", max_pair_tokens=1024, batch_size=4)
            reranker.score.side_effect = lambda question, candidates: [
                RelevanceScore(chunk_id=c.chunk_id, score=3.25) for c in candidates
            ]
            app.state.resources = AppResources(
                settings=Settings(
                    _env_file=None, openai_api_key="offline-browser-test",
                    chunking_strategy="parent_child", chunk_max_tokens=16, rerank_enabled=True,
                ),
                assets=PdfAssets(Path(directory)),
                pdf_parser=Mock(parse=Mock(return_value=PdfExtraction.model_validate_json(
                    (Path(__file__).resolve().parents[1] / "evals/check-runs/20260926-pdf-parser-selection/adapter-2/apple-fy24.json").read_text()
                ))),
                sessions=sessions,
                store=store,
                embeddings=embeddings,
                llm=llm,
                streaming_llm=streaming_llm,
                planner=PlannerClient(planner_sdk, "offline-planner", PlanningOptions(), "cl100k_base"),
                reranker=reranker,
            )
            yield


app = create_app()
app.router.lifespan_context = lifespan
