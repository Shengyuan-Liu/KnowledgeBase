"""Exercise reranking before selection, parent packing, and saved chat evidence."""

import json
from unittest.mock import Mock

import pytest
import tiktoken
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from knowledgebase.api import app as api_module
from knowledgebase.config import RetrievalOptions
from knowledgebase.rag.context import build_context
from knowledgebase.rag.retrieval import retrieve_evidence
from knowledgebase.schemas import RelevanceScore
from knowledgebase.services.files import ingest_file
from knowledgebase.storage.models import MessageRecord
from knowledgebase.storage.operations import get_chunks, get_parents, update_file_status


def score_facts(question, candidates):
    return [RelevanceScore(chunk_id=c.chunk_id, score=3.75 if "3.0" in c.text or "66%" in c.text else -2.5)
            for c in candidates]


def reranker():
    return Mock(model="offline-reranker", model_revision="test-revision", device="cpu", max_pair_tokens=1024, batch_size=4, score=Mock(side_effect=score_facts))


def test_rerank_precedes_top_k_parent_deduplication_and_budget(storage, embeddings):
    sessions, store, _ = storage
    pointer = "# Requirements\n\n" + "See the requirements page for more details. " * 8
    facts = "# Progress\n\nMaintain GPA 3.0 each semester.\n\nComplete 66% of attempted credits.\n"
    first = ingest_file("pointer.md", pointer.encode(), sessions, embeddings, store,
                        chunk_max_tokens=12, parent_max_tokens=128)
    second = ingest_file("facts.md", facts.encode(), sessions, embeddings, store,
                         chunk_max_tokens=12, parent_max_tokens=128)
    scorer = reranker()
    options = RetrievalOptions(rerank_enabled=True)
    with sessions() as session:
        children = get_chunks(session, second)
        parent = get_parents(session, second)[0]
        store.upsert_chunks(children, [[0, 1] for _ in children])
        baseline = retrieve_evidence("requirements", session, embeddings, store, top_k=1)
        assert baseline.chunks[0].chunk.file_id == first
        one = retrieve_evidence("requirements", session, embeddings, store, top_k=1,
                                retrieval_options=options, reranker_client=scorer)
        assert one.chunks[0].chunk.file_id == second
        assert one.chunks[0].fusion.rank > 1
        assert one.chunks[0].rerank.rerank_rank == 1
        assert one.chunks[0].chunk.text == parent.text
        budget = len(tiktoken.get_encoding("cl100k_base").encode_ordinary(build_context(one.chunks)))
        packed = retrieve_evidence("requirements", session, embeddings, store, top_k=10,
                                   evidence_max_tokens=budget, retrieval_options=options, reranker_client=scorer)
        assert [s.chunk.file_id for s in packed.chunks] == [second]
        assert packed.chunks[0].chunk.text == facts
        assert len(packed.chunks[0].matched_child_ids) >= 2
        assert packed.chunks[0].rerank.chunk_id == packed.chunks[0].matched_child_ids[0]
        assert any(item.file_id == first for item in packed.diagnostics.excluded)
        assert packed.diagnostics.evidence_tokens == budget
        trace = packed.diagnostics.rerank
        assert len(trace.candidates) > 1
        assert trace.candidates[0].rank == 1
        assert trace.matches[0].rank > 1
        assert packed.diagnostics.rerank_seconds >= 0
    with sessions.begin() as session:
        update_file_status(session, second, "failed")
    with sessions() as session:
        ready = retrieve_evidence("requirements", session, embeddings, store,
                                  retrieval_options=options, reranker_client=scorer)
        assert all(not c.chunk_id.startswith(second) for c in ready.diagnostics.rerank.candidates)


def test_disabled_and_empty_library_do_not_call_reranker(storage, embeddings):
    sessions, store, _ = storage
    client = reranker()
    with sessions() as session:
        empty = retrieve_evidence("Question", session, embeddings, store,
                                  retrieval_options=RetrievalOptions(rerank_enabled=True), reranker_client=client)
        assert empty.chunks == []
    ingest_file("facts.txt", b"Maintain GPA 3.0.", sessions, embeddings, store)
    with sessions() as session:
        disabled = retrieve_evidence("GPA", session, embeddings, store, reranker_client=client)
    assert disabled.diagnostics.rerank is None
    assert disabled.chunks[0].rerank is None
    client.score.assert_not_called()


def test_enabled_reranking_requires_a_client(storage, embeddings):
    sessions, store, _ = storage
    with sessions() as session, pytest.raises(ValueError, match="requires a reranker client"):
        retrieve_evidence("Question", session, embeddings, store,
                          retrieval_options=RetrievalOptions(rerank_enabled=True))


@pytest.fixture(params=["child", "parent"])
def rerank_app(configured_app, tmp_path, monkeypatch, request):
    app, embeddings, sdk = configured_app
    (tmp_path / ".env").write_text(
        f"RERANK_UNIT={request.param}\n"
        "RERANK_ENABLED=true\nRERANK_MODEL=custom-reranker\nRERANK_CANDIDATE_LIMIT=7\n"
        "RERANK_MAX_INPUT_TOKENS=1000\nCHUNK_MAX_TOKENS=12\nPARENT_MAX_TOKENS=128\n"
        "EVIDENCE_MAX_TOKENS=256\nRETRIEVAL_TOP_K=2\n"
    )

    sdk.reranker = reranker()
    sdk.reranker.model = "custom-reranker"
    monkeypatch.setattr(api_module, "RerankerClient", Mock(return_value=sdk.reranker))
    sdk.responses.create.side_effect = lambda **kwargs: Mock(output_text=(
        "Resolved GPA question" if kwargs["input"][0]["content"].startswith("Rewrite") else "GPA 3.0 and 66%. [1]"
    ))
    stream_calls = []

    async def stream(messages):
        stream_calls.append(messages)
        yield "GPA 3.0 and 66%. [1]"

    monkeypatch.setattr(api_module, "StreamingLLMClient", Mock(return_value=Mock(stream=stream)))
    return app, embeddings, sdk, stream_calls


def ask(client, streaming, conversation_id=None):
    response = client.post("/api/chat/stream" if streaming else "/api/chat", json={
        "question": "And the other requirement?" if conversation_id else "GPA requirements",
        "request_id": "rerank-test", "conversation_id": conversation_id,
    })
    if not streaming:
        return response, []
    events = [{"event": frame.split("\n")[0].removeprefix("event: "),
               **json.loads(frame.split("\ndata: ")[1])}
              for frame in response.text.strip().split("\n\n")]
    return response, events


@pytest.mark.parametrize("streaming", [False, True])
def test_json_and_sse_persist_exact_reranked_evidence_and_restore_after_restart_and_delete(rerank_app, streaming):
    app, embeddings, sdk, stream_calls = rerank_app
    text = "# Guide\n\nSee the requirements page.\n\n# Progress\n\nMaintain GPA 3.0 each semester.\n\nComplete 66% of attempted credits.\n"
    with TestClient(app) as client:
        file_id = client.post("/api/files", files={"file": ("guide.md", text.encode())}).json()["file_id"]
        response, events = ask(client, streaming)
        assert response.status_code == 200
        result = events[-1] if streaming else response.json()
        if streaming:
            assert result["event"] == "complete"
            assert next(e["sources"] for e in events if e["event"] == "sources") == result["sources"]
        trace = result["retrieval"]["rerank"]
        if result["retrieval"]["options"]["rerank_unit"] == "parent":
            assert all(c["scoring_parent_id"] for c in trace["candidates"])
            assert result["sources"][0]["rerank"]["scoring_parent_id"] == result["sources"][0]["parent_id"]
        assert trace["model"] == "custom-reranker"
        assert trace["candidate_limit"] == 7 and trace["max_input_tokens"] == 1000
        assert trace["top_k"] == 2
        api_module.RerankerClient.assert_called_with("custom-reranker", device="auto", batch_size=4, max_pair_tokens=1024)
        assert trace["score_kind"] == "logit"
        assert result["sources"][0]["rerank"]["rerank_score"] == 3.75
        source = result["sources"][0]
        assert source["rerank"]["rerank_rank"] == 1
        assert source["fusion"]["rank"] == source["rerank"]["rank"]
        assert source["text"] == text[source["start_offset"]:source["end_offset"]]
        assert "3.0" in source["text"] and "66%" in source["text"]
        prompt = stream_calls[-1] if streaming else sdk.responses.create.call_args.kwargs["input"]
        assert source["text"] in prompt[0]["content"]
        ask(client, streaming, result["conversation_id"])
        assert sdk.reranker.score.call_args.args[0] == "Resolved GPA question"
        assert sdk.reranker.model == "custom-reranker"
    with TestClient(api_module.create_app()) as client:
        assert client.delete(f"/api/files/{file_id}").status_code == 204
        saved = client.get(f"/api/conversations/{result['conversation_id']}").json()["messages"][1]
        assert saved["retrieval"] == result["retrieval"]
        assert saved["sources"] == [{**s, "file_deleted": True} for s in result["sources"]]
        before_calls = sdk.reranker.score.call_count
        response, events = ask(client, streaming)
        empty = events[-1] if streaming else response.json()
        assert empty["sources"] == []
        assert sdk.reranker.score.call_count == before_calls


@pytest.mark.parametrize("streaming", [False, True])
@pytest.mark.parametrize("failure", ["provider", "input_budget"])
def test_rerank_failure_does_not_generate_or_save_an_exchange(rerank_app, streaming, failure):
    app, _, sdk, stream_calls = rerank_app
    with TestClient(app) as client:
        client.post("/api/files", files={"file": ("notes.txt", b"Maintain GPA 3.0.")})
        if failure == "provider":
            sdk.reranker.score.side_effect = RuntimeError("Scoring failed")
        else:
            app.state.resources.settings.rerank_max_input_tokens = 1
        response, events = ask(client, streaming)
        if streaming:
            assert [e["event"] for e in events] == ["start", "error"]
        else:
            assert response.status_code == 500
        sdk.responses.create.assert_not_called()
        assert stream_calls == []
        with app.state.resources.sessions() as session:
            assert session.scalar(select(func.count()).select_from(MessageRecord)) == 0
        if failure == "input_budget":
            sdk.reranker.score.assert_not_called()


def test_parent_scoring_keeps_other_region_when_siblings_dominate_child_top_k(storage, embeddings):
    sessions, store, _ = storage
    work = '# Work\n\n' + '\n\n'.join(f'Working students have workload requirement {i}.' for i in range(5))
    summer = '# Enrollment\n\nContinuous enrollment excludes summer.'
    ids = [ingest_file(name, text.encode(), sessions, embeddings, store,
                      chunk_max_tokens=12, parent_max_tokens=128)
           for name, text in [('work.md', work), ('summer.md', summer)]]
    scorer = reranker()
    scorer.score.side_effect = lambda question, candidates: [
        RelevanceScore(chunk_id=c.chunk_id, score=10 if 'Working' in c.text else 5 if 'summer' in c.text else 0)
        for c in candidates]
    with sessions() as session:
        control = retrieve_evidence('working enrollment', session, embeddings, store, top_k=2,
                                    retrieval_options=RetrievalOptions(rerank_enabled=True), reranker_client=scorer)
        result = retrieve_evidence('working enrollment', session, embeddings, store, top_k=2,
            retrieval_options=RetrievalOptions(rerank_enabled=True, rerank_unit='parent', rerank_candidate_limit=2),
            reranker_client=scorer)
        canonical = {c.chunk_id: c for file_id in ids for c in get_chunks(session, file_id)}
    assert {c.file_id for c in control.diagnostics.candidates} == {ids[0]}
    assert [s.chunk.text for s in result.chunks] == [work, summer]
    scored = result.diagnostics.rerank.candidates
    assert len(scored) == 2 and len({c.scoring_parent_id for c in scored}) == 2
    assert {c.text for c in scored} == {work, summer}
    for candidate in result.diagnostics.candidates:
        assert candidate.text == canonical[candidate.chunk_id].text
        assert candidate.rerank.scoring_parent_id == candidate.parent_id
        assert candidate.rerank.rank == candidate.fusion.rank


def test_parent_mode_preserves_flat_chunks_without_fabricating_a_parent(storage, embeddings):
    from knowledgebase.schemas import Chunk
    from knowledgebase.storage.operations import create_file, save_chunks
    sessions, store, _ = storage
    flat = Chunk(chunk_id='flat', file_id='flat', index=0, text='GPA 3.0', start_offset=0, end_offset=7)
    with sessions.begin() as session:
        create_file(session, 'flat', 'flat.txt')
        save_chunks(session, [flat])
        update_file_status(session, 'flat', 'ready')
    store.upsert_chunks([flat], [[1, 0]])
    with sessions() as session:
        result = retrieve_evidence('GPA', session, embeddings, store,
            retrieval_options=RetrievalOptions(rerank_enabled=True, rerank_unit='parent'), reranker_client=reranker())
    assert result.chunks[0].chunk == flat
    assert result.chunks[0].rerank.scoring_parent_id is None
    assert result.diagnostics.rerank.candidates[0].text == flat.text
