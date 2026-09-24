"""Verify route integration, source provenance, and persisted library lifecycle."""

import json
from unittest.mock import Mock

import pytest
import tiktoken
from fastapi.testclient import TestClient

from knowledgebase.api import app as api_module
from knowledgebase.config import RetrievalOptions
from knowledgebase.rag.context import build_context
from knowledgebase.rag.retrieval import retrieve_evidence
from knowledgebase.schemas import Chunk
from knowledgebase.services.files import ingest_file
from knowledgebase.storage.operations import (
    create_file, get_chunks, save_chunks, update_file_status,
)


def add_flat(session, store, identity, text, vector, status="ready"):
    create_file(session, identity, f"{identity}.txt")
    chunk = Chunk(chunk_id=identity, file_id=identity, text=text, index=0,
                  start_offset=0, end_offset=len(text))
    save_chunks(session, [chunk])
    store.upsert_chunks([chunk], [vector])
    update_file_status(session, identity, status)
    return chunk


@pytest.mark.parametrize("strategy,expected", [("vector", "a"), ("hybrid", "b")])
def test_fusion_selects_children_after_both_route_windows(storage, embeddings, strategy, expected):
    sessions, store, _ = storage
    with sessions.begin() as session:
        add_flat(session, store, "a", "unrelated", [1, 0])
        add_flat(session, store, "b", "needle needle", [0.8, 0.6])
        add_flat(session, store, "c", "needle other", [0, 1])
    observed = Mock(wraps=store)
    with sessions() as session:
        result = retrieve_evidence("needle", session, embeddings, observed, top_k=1,
                                  retrieval_options=RetrievalOptions(strategy=strategy, candidate_limit=2))
    assert [item.chunk.chunk_id for item in result.chunks] == [expected]
    assert observed.search.call_args.kwargs["top_k"] == (2 if strategy == "hybrid" else 1)
    if strategy == "hybrid":
        assert [m.chunk_id for m in result.diagnostics.bm25_matches] == ["b", "c"]
        assert [m.chunk_id for m in result.diagnostics.vector_matches] == ["a", "b"]
        assert [m.chunk_id for m in result.diagnostics.fused_matches] == ["b", "a", "c"]
        assert result.chunks[0].fusion.rrf_score == pytest.approx(1 / 61 + 1 / 62)
        assert result.chunks[0].fusion.vector_rank == 2
        assert result.chunks[0].fusion.bm25_rank == 1
        assert result.chunks[0].distance == pytest.approx(0.2)
    else:
        assert result.diagnostics.bm25_matches == result.diagnostics.fused_matches == []
        assert result.chunks[0].fusion is None


def test_ready_filter_precedes_both_route_limits_and_bm25_statistics(storage, embeddings):
    sessions, store, _ = storage
    options = RetrievalOptions(candidate_limit=1)
    with sessions.begin() as session:
        add_flat(session, store, "ready", "needle", [0, 1])
    with sessions() as session:
        baseline = retrieve_evidence("needle", session, embeddings, store, retrieval_options=options)
    with sessions.begin() as session:
        for status in ("processing", "failed"):
            add_flat(session, store, status, "needle needle needle", [1, 0], status)
    with sessions() as session:
        result = retrieve_evidence("needle", session, embeddings, store, retrieval_options=options)
    assert result.model_dump(exclude={"diagnostics": {"packing_seconds"}}) == baseline.model_dump(exclude={"diagnostics": {"packing_seconds"}})
    assert [hit.chunk_id for hit in result.diagnostics.vector_matches] == ["ready"]


def test_parent_keeps_best_fused_child_provenance_when_sibling_has_vector_hit(storage, embeddings):
    sessions, store, _ = storage
    text = "# Plant\n\norchid\n\nKeep indoors.\n\nAsk the gardener.\n"
    file_id = ingest_file("plant.md", text.encode(), sessions, embeddings, store,
                          chunk_max_tokens=5, parent_max_tokens=128)
    with sessions() as session:
        children = get_chunks(session, file_id)
        lexical = next(c for c in children if "orchid" in c.text)
        vector = children[-1]
        assert lexical.index < vector.index
        store.upsert_chunks(children, [[1, 0] if c == vector else [0, 1] for c in children])
        result = retrieve_evidence("orchid", session, embeddings, store, top_k=2,
                                   retrieval_options=RetrievalOptions(candidate_limit=1))
    assert len(result.chunks) == 1
    source = result.chunks[0]
    assert source.chunk.text == text
    assert source.matched_child_ids == [lexical.chunk_id, vector.chunk_id]
    assert source.distance is None
    assert source.fusion.chunk_id == lexical.chunk_id
    assert source.fusion.rank == 1
    assert result.diagnostics.candidates[1].fusion.vector_rank == 1


@pytest.mark.parametrize("streaming", [False, True])
def test_lexical_only_parent_evidence_survives_restart_and_deletion(configured_app, tmp_path, monkeypatch, streaming):
    app, embeddings, sdk = configured_app
    (tmp_path / ".env").write_text(
        "RETRIEVAL_STRATEGY=hybrid\nRETRIEVAL_CANDIDATE_LIMIT=1\nRETRIEVAL_TOP_K=2\n"
    )
    sdk.responses.create.return_value = Mock(output_text="Keep the orchid indoors. [1] [2]")
    prompts = []

    async def stream(messages):
        prompts.append(messages)
        yield "Keep the orchid indoors. [1] [2]"

    streamer = Mock()
    streamer.stream = stream
    monkeypatch.setattr(api_module, "StreamingLLMClient", Mock(return_value=streamer))
    text = "# Orchid\r\n\r\nKeep the orchid indoors.\r\n"

    def ask(client):
        response = client.post("/api/chat/stream" if streaming else "/api/chat",
                               json={"question": "orchid", "request_id": "hybrid-test"})
        assert response.status_code == 200
        if not streaming:
            return response.json()
        events = [{"event": frame.split("\n")[0].removeprefix("event: "), **json.loads(frame.split("\ndata: ")[1])}
                  for frame in response.text.strip().split("\n\n")]
        assert events[-1]["event"] == "complete"
        assert next(e["sources"] for e in events if e["event"] == "sources") == events[-1]["sources"]
        return events[-1]

    with TestClient(app) as client:
        lexical_id = client.post("/api/files", files={"file": ("orchid.md", text.encode())}).json()["file_id"]
        other_id = client.post("/api/files", files={"file": ("other.txt", b"Visit the library.")}).json()["file_id"]
        with app.state.resources.sessions() as session:
            children = get_chunks(session, lexical_id)
        app.state.resources.store.upsert_chunks(children, [[0, 1] for _ in children])
        first = ask(client)
        source = next(s for s in first["sources"] if s["file_id"] == lexical_id)
        assert source["distance"] is None
        assert source["fusion"]["vector_rank"] is None
        assert source["fusion"]["bm25_rank"] == 1
        assert source["fusion"]["rrf_score"] == pytest.approx(1 / 61)
        assert source["text"] == text
        assert source["parent_id"] == source["chunk_id"]
        assert source["matched_child_ids"] == [children[0].chunk_id]
        assert first["retrieval"]["options"]["strategy"] == "hybrid"
        prompt = prompts[-1] if streaming else sdk.responses.create.call_args.kwargs["input"]
        assert text in prompt[-1]["content"]
        before_embedding_calls = embeddings.embed_documents.call_count
    reopened = api_module.create_app()
    with TestClient(reopened) as client:
        after = ask(client)
        assert after["sources"] == first["sources"]
        assert {k: v for k, v in after["retrieval"].items() if k != "packing_seconds"} == {
            k: v for k, v in first["retrieval"].items() if k != "packing_seconds"
        }
        assert embeddings.embed_documents.call_count == before_embedding_calls
        assert client.delete(f"/api/files/{lexical_id}").status_code == 204
        remaining = ask(client)
        assert remaining["retrieval"]["bm25_matches"] == []
        assert {s["file_id"] for s in remaining["sources"]} == {other_id}
        saved = client.get(f"/api/conversations/{first['conversation_id']}").json()["messages"][-1]
        assert saved["retrieval"] == first["retrieval"]
        assert saved["sources"] == [{**s, "file_deleted": s["file_id"] == lexical_id} for s in first["sources"]]
        assert client.delete(f"/api/files/{other_id}").status_code == 204
        before_query_calls = embeddings.embed_query.call_count
        assert ask(client)["sources"] == []
        assert embeddings.embed_query.call_count == before_query_calls


def test_budget_keeps_fused_order_and_records_whole_region_exclusion(storage, embeddings):
    sessions, store, _ = storage
    with sessions.begin() as session:
        a = add_flat(session, store, "a", "needle needle", [0, 1])
        add_flat(session, store, "b", "unrelated text", [1, 0])
    with sessions() as session:
        full = retrieve_evidence("needle", session, embeddings, store, top_k=2,
                                 retrieval_options=RetrievalOptions(candidate_limit=1))
        assert full.chunks[0].chunk == a
        budget = len(tiktoken.get_encoding("cl100k_base").encode_ordinary(build_context(full.chunks[:1])))
        packed = retrieve_evidence("needle", session, embeddings, store, top_k=2,
                                   evidence_max_tokens=budget, retrieval_options=RetrievalOptions(candidate_limit=1))
    assert packed.chunks == full.chunks[:1]
    assert packed.diagnostics.evidence_tokens == budget
    assert [hit.chunk_id for hit in packed.diagnostics.excluded] == ["b"]
    assert len(packed.diagnostics.candidates) == len(packed.diagnostics.fused_matches) == 2
