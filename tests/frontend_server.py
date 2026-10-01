"""Isolated real HTTP/storage server for frontend browser tests; no model calls."""

from contextlib import asynccontextmanager
import json
from pathlib import Path
import re
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
from knowledgebase.schemas import (
    PdfExtraction, RelevanceScore,
)


def payload_catalog(payload):
    """Read the offline provider's passage choices from annotated source lines."""
    entries = []
    for line in payload["context"].splitlines(keepends=True):
        if line.startswith("Source metadata: "):
            file_name = json.loads(line.removeprefix("Source metadata: "))["file_name"]
        match = re.match(r"\[(p\d+)\] (.*)", line, flags=re.DOTALL)
        if match:
            entries.append({"evidence_id": match[1], "file_name": file_name, "text": match[2]})
    return entries


async def stream_fixture(messages):
    """Keep the cancellation fixture open until the browser disconnects."""
    if "prize winner" in messages[0]["content"].lower():
        yield "Mira Cole works at Birch Institute. [2]"
        return
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
    payload = json.loads(kwargs["input"][-1]["content"])
    question = payload["original_question"]
    sleep(2 if question.startswith("Stop planning") else 0.3)
    if "total net sales" in question.lower():
        if kwargs["text"]["format"]["name"] == "retrieval_plan":
            decision = {"route": "direct", "requirements": [], "queries": [], "dependencies": []}
        else:
            refs = [{"evidence_id": e["evidence_id"]} for e in payload_catalog(payload)
                    if "94,930" in e["text"]]
            decision = {"requirements": [{"requirement_id": "answer", "status": "supported" if refs else "missing",
                "gap": "" if refs else "Net sales were not retained.", "references": refs}], "queries": []}
        return SimpleNamespace(status="completed", output_text=json.dumps(decision),
                               model="offline-planner", id="offline-pdf-plan", usage=None)
    if kwargs["text"]["format"]["name"] == "evidence_assessment":
        if question.startswith("Stop assessment"):
            sleep(2)
        requirements = []
        for item in payload["requirements"]:
            name, quote = {
                "winner": ("award.txt", "The Aster Prize winner is Mira Cole."),
                "employer": ("staff.txt", "Mira Cole works at Birch Institute."),
                "hours": ("hours.txt", "The library closes at 5 PM."),
                "access": ("hours.txt", "Students can enter with a library card."),
            }[item["requirement_id"]]
            excerpt = next((e for e in payload_catalog(payload) if e["file_name"] == name and quote in e["text"]), None)
            supported = excerpt is not None
            requirements.append({"requirement_id": item["requirement_id"],
                "status": "supported" if supported else "missing",
                "gap": "" if supported else "No supporting excerpt.",
                "references": [{"evidence_id": excerpt["evidence_id"]}] if supported else []})
        return SimpleNamespace(status="completed", output_text=json.dumps({"requirements": requirements, "queries": []}),
                               model="offline-planner", id="offline-assessment", usage=None)
    if kwargs["text"]["format"]["name"] == "dependency_targets":
        if question.startswith("Stop binding"):
            sleep(2)
        item = payload["pending_queries"][0]
        excerpt = item["evidence"][0]
        decision = {"decisions": [{"query_id": item["query_id"], "status": "resolved", "target": "Mira Cole",
            "references": [{"evidence_id": excerpt["evidence_id"], "quote": excerpt["text"]}]}]}
        return SimpleNamespace(status="completed", output_text=json.dumps(decision),
                               model="offline-planner", id="offline-binding", usage=None)
    if "prize winner" in question.lower():
        decision = {"route": "dependent", "requirements": [
            {"requirement_id": "winner", "description": "Prize winner"},
            {"requirement_id": "employer", "description": "Winner's institute"}],
            "queries": [{"query_id": "winner", "text": 'In "award.txt", who won the Aster Prize?', "requirement_ids": ["winner"]}],
            "dependencies": [{"query_id": "employer", "query_template": 'In "staff.txt", who employs {target}?',
                "requirement_ids": ["employer"], "depends_on": ["winner"]}]}
        return SimpleNamespace(status="completed", output_text=json.dumps(decision),
                               model="offline-planner", id="offline-plan", usage=None)
    decision = {"route": "decomposed", "dependencies": [], "requirements": [
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
