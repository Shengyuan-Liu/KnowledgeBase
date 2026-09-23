"""Exercise child indexing, parent evidence, budget accounting, and saved answers."""

import json
from unittest.mock import MagicMock, Mock

import pytest
import tiktoken
from fastapi.testclient import TestClient
from sqlalchemy import select

from knowledgebase.api import app as api_module
from knowledgebase.rag.context import build_context
from knowledgebase.rag.generation import INSUFFICIENT_EVIDENCE
from knowledgebase.rag.retrieval import retrieve_evidence
from knowledgebase.schemas import ChildChunk, VectorMatch
from knowledgebase.services.chat import answer_in_conversation
from knowledgebase.services.files import delete_file, ingest_file
from knowledgebase.storage.models import ChildParentRecord, RetrievalSnapshotRecord
from knowledgebase.storage.operations import (
    get_chunks, get_conversation_detail, get_document_source, get_files, get_parents,
)


SOURCE = (
    "# Library\r\n\r\nThe café closes at 5 PM.\r\n\r\n"
    "- Weekend visits require a reservation.\r\n"
    "- Bring your library card.\r\n"
    "\r\n# Contact\r\n\r\nEmail the librarian.\r\n"
)


def index_parent_file(storage, embeddings, text=SOURCE):
    sessions, store, _ = storage
    file_id = ingest_file(
        "guide.md", text.encode(), sessions, embeddings, store,
        chunking_strategy="parent_child", chunk_max_tokens=12, parent_max_tokens=128,
    )
    with sessions() as session:
        return file_id, get_parents(session, file_id), get_chunks(session, file_id)


def ranked_store(store, children, distances):
    observed = Mock(wraps=store)
    observed.search.return_value = [
        VectorMatch(chunk_id=child.chunk_id, distance=distance)
        for child, distance in zip(children, distances, strict=True)
    ]
    return observed


def test_ingestion_indexes_only_children_and_one_hit_expands_exact_parent(storage, embeddings):
    sessions, store, collection = storage
    file_id, parents, children = index_parent_file(storage, embeddings)
    assert len(parents) == 2
    assert len(children) > len(parents)
    assert all(isinstance(child, ChildChunk) for child in children)
    assert set(collection.get()["ids"]) == {child.chunk_id for child in children}
    embeddings.embed_documents.assert_called_once_with([child.text for child in children])
    selected = next(child for child in children if "5 PM" in child.text)
    store.upsert_chunks(children, [[1.0, 0.0] if child == selected else [0.0, 1.0] for child in children])
    with sessions() as session:
        evidence = retrieve_evidence("Closing time?", session, embeddings, store, top_k=1)
        assert get_document_source(session, file_id).text == SOURCE
    assert len(evidence.chunks) == 1
    result = evidence.chunks[0]
    assert result.parent_id == parents[0].parent_id == result.chunk.chunk_id
    assert result.matched_child_ids == [selected.chunk_id]
    assert result.distance == pytest.approx(0.0)
    assert result.chunk.text == SOURCE[parents[0].start_offset:parents[0].end_offset]
    assert "reservation" in result.chunk.text and "reservation" not in selected.text
    assert result.chunk.heading_path == ["Library"]
    assert evidence.diagnostics.candidates[0].text == selected.text


def test_parent_deduplication_best_child_rank_and_mixed_flat_files(storage, embeddings):
    sessions, store, _ = storage
    _, parents, children = index_parent_file(storage, embeddings)
    first = [child for child in children if child.parent_id == parents[0].parent_id]
    second = next(child for child in children if child.parent_id == parents[1].parent_id)
    flat_id = ingest_file("old.txt", b"Existing flat evidence.", sessions, embeddings, store)
    with sessions() as session:
        flat = get_chunks(session, flat_id)[0]
        matches = ranked_store(store, [first[0], second, flat, first[1]], [0.4, 0.2, 0.3, 0.1])
        evidence = retrieve_evidence("Question?", session, embeddings, matches, top_k=4)
    assert [item.chunk.chunk_id for item in evidence.chunks] == [parents[0].parent_id, parents[1].parent_id, flat.chunk_id]
    assert [item.distance for item in evidence.chunks] == [0.1, 0.2, 0.3]
    assert evidence.chunks[0].matched_child_ids == [first[1].chunk_id, first[0].chunk_id]
    assert evidence.chunks[2].parent_id is None
    assert evidence.chunks[2].matched_child_ids == []
    assert [candidate.chunk_id for candidate in evidence.diagnostics.candidates] == [first[1].chunk_id, second.chunk_id, flat.chunk_id, first[0].chunk_id]


def test_equal_distance_candidates_use_stable_identity_order(storage, embeddings):
    sessions, store, _ = storage
    _, parents, children = index_parent_file(storage, embeddings)
    selected = [next(c for c in children if c.parent_id == p.parent_id) for p in parents]
    with sessions() as session:
        evidence = retrieve_evidence("Question?", session, embeddings, ranked_store(store, selected[::-1], [0.1, 0.1]))
    assert [candidate.chunk_id for candidate in evidence.diagnostics.candidates] == sorted(c.chunk_id for c in selected)
    assert [item.parent_id for item in evidence.chunks] == [p.parent_id for p in parents]


def test_budget_counts_labels_and_separators_without_truncating_parents(storage, embeddings):
    sessions, store, _ = storage
    _, parents, children = index_parent_file(storage, embeddings)
    selected = [next(c for c in children if c.parent_id == p.parent_id) for p in parents]
    matches = ranked_store(store, selected, [0.1, 0.2])
    encoding = tiktoken.get_encoding("cl100k_base")
    with sessions() as session:
        full = retrieve_evidence("Question?", session, embeddings, matches)
        exact = len(encoding.encode_ordinary(build_context(full.chunks)))
        packed = retrieve_evidence("Question?", session, embeddings, matches, evidence_max_tokens=exact)
        assert packed.chunks == full.chunks
        assert packed.diagnostics.evidence_tokens == exact
        short = retrieve_evidence("Question?", session, embeddings, matches, evidence_max_tokens=exact - 1)
        assert [item.parent_id for item in short.chunks] == [parents[0].parent_id]
        assert short.diagnostics.excluded[0].chunk_id == parents[1].parent_id
        small_budget = len(encoding.encode_ordinary(build_context([full.chunks[1]])))
        skipped = retrieve_evidence("Question?", session, embeddings, matches, evidence_max_tokens=small_budget)
    assert [item.parent_id for item in skipped.chunks] == [parents[1].parent_id]
    assert skipped.chunks[0].chunk.text == parents[1].text
    assert skipped.diagnostics.evidence_tokens == small_budget
    assert skipped.diagnostics.excluded[0].model_dump() == {
        "chunk_id": parents[0].parent_id, "file_id": parents[0].file_id,
        "reason": "context_budget", "token_count": parents[0].token_count,
    }
    assert len(skipped.diagnostics.candidates) == 2


def test_no_fitting_evidence_skips_generation_and_persists_exclusions(storage, embeddings):
    sessions, store, _ = storage
    _, parents, children = index_parent_file(storage, embeddings)
    llm = Mock()
    result = answer_in_conversation(
        "Question?", sessions, embeddings, ranked_store(store, children[:1], [0.1]), llm,
        evidence_max_tokens=1,
    )
    assert result.answer == INSUFFICIENT_EVIDENCE
    assert result.sources == []
    llm.generate.assert_not_called()
    assert result.retrieval.evidence_tokens == 0
    assert result.retrieval.excluded[0].chunk_id == parents[0].parent_id
    with sessions() as session:
        saved = get_conversation_detail(session, result.conversation_id).messages[-1]
        assert saved.retrieval == result.retrieval


def test_expanded_sources_numbering_prompt_and_post_delete_history(storage, embeddings):
    sessions, store, _ = storage
    file_id, parents, children = index_parent_file(storage, embeddings)
    selected = [next(c for c in children if c.parent_id == p.parent_id) for p in parents]
    llm = Mock()
    llm.generate.return_value = "Reserve weekend visits. [1] Email the librarian. [2]"
    result = answer_in_conversation("Visit details?", sessions, embeddings, ranked_store(store, selected, [0.1, 0.2]), llm)
    assert [source.source_id for source in result.sources] == [1, 2]
    assert [source.text for source in result.sources] == [parent.text for parent in parents]
    assert result.citation_check.valid_source_ids == [1, 2]
    prompt = llm.generate.call_args.args[0][-1]["content"]
    assert f"[1]\n{parents[0].text}\n\n[2]\n{parents[1].text}" in prompt
    delete_file(file_id, sessions, store)
    with sessions() as session:
        saved = get_conversation_detail(session, result.conversation_id).messages[-1]
    assert saved.retrieval == result.retrieval
    assert [s.model_dump(exclude={"file_deleted"}) for s in saved.sources] == [s.model_dump() for s in result.sources]
    assert all(s.file_deleted for s in saved.sources)


def test_failed_vector_write_rolls_back_parent_storage_and_cleans_partial_index(storage, embeddings):
    sessions, store, collection = storage
    kept_id, parents, children = index_parent_file(storage, embeddings)
    failing = Mock(wraps=store)

    def fail_after_write(chunks, vectors):
        store.upsert_chunks(chunks[:1], vectors[:1])
        raise RuntimeError("Index write failed")

    failing.upsert_chunks.side_effect = fail_after_write
    with pytest.raises(RuntimeError, match="Index write failed"):
        index_parent_file((sessions, failing, collection), embeddings)
    with sessions() as session:
        failed = next(file for file in get_files(session) if file.file_id != kept_id)
        assert failed.status == "failed"
        assert get_parents(session, failed.file_id) == get_chunks(session, failed.file_id) == []
        assert get_document_source(session, failed.file_id) is None
        assert get_parents(session, kept_id) == parents
        assert {link.chunk_id for link in session.scalars(select(ChildParentRecord))} == {c.chunk_id for c in children}
    assert set(collection.get()["ids"]) == {c.chunk_id for c in children}


@pytest.mark.parametrize("streaming", [False, True])
def test_api_parent_evidence_and_diagnostics_survive_restart_and_deletion(configured_app, tmp_path, monkeypatch, streaming):
    app, _, sdk = configured_app
    (tmp_path / ".env").write_text("CHUNKING_STRATEGY=parent_child\nCHUNK_MAX_TOKENS=12\nPARENT_MAX_TOKENS=128\nEVIDENCE_MAX_TOKENS=256\nRETRIEVAL_TOP_K=1\n")
    sdk.responses.create.return_value = Mock(output_text="At 5 PM. [1]")
    async_sdk = MagicMock()
    monkeypatch.setattr(api_module, "AsyncOpenAI", Mock(return_value=async_sdk))
    prompts = []

    async def stream(messages):
        prompts.append(messages)
        yield "At 5 PM. [1]"

    streamer = Mock()
    streamer.stream = stream
    monkeypatch.setattr(api_module, "StreamingLLMClient", Mock(return_value=streamer))
    with TestClient(app) as client:
        file_id = client.post("/api/files", files={"file": ("guide.md", SOURCE.encode())}).json()["file_id"]
        with app.state.resources.sessions() as session:
            parents = get_parents(session, file_id)
            children = get_chunks(session, file_id)
        chosen = next(c for c in children if "5 PM" in c.text)
        app.state.resources.store.upsert_chunks(children, [[1.0, 0.0] if c == chosen else [0.0, 1.0] for c in children])
        response = client.post("/api/chat/stream" if streaming else "/api/chat", json={"question": "Closing time?", "request_id": "parent-test"})
        assert response.status_code == 200
        if streaming:
            frames = response.text.strip().split("\n\n")
            assert frames[-1].startswith("event: complete\n")
            result = json.loads(frames[-1].split("\ndata: ")[1])
            sources_event = next(frame for frame in frames if frame.startswith("event: sources\n"))
            assert json.loads(sources_event.split("\ndata: ")[1])["sources"] == result["sources"]
            prompt = prompts[0]
        else:
            result = response.json()
            prompt = sdk.responses.create.call_args.kwargs["input"]
        assert parents[0].text in prompt[-1]["content"]
        assert result["sources"][0]["text"] == parents[0].text
        assert result["sources"][0]["matched_child_ids"] == [chosen.chunk_id]
        assert result["retrieval"]["candidates"][0]["text"] == chosen.text
    reopened = api_module.create_app()
    with TestClient(reopened) as client:
        assert client.delete(f"/api/files/{file_id}").status_code == 204
        saved = client.get(f"/api/conversations/{result['conversation_id']}").json()["messages"][-1]
        assert saved["sources"] == [{**source, "file_deleted": True} for source in result["sources"]]
        assert saved["retrieval"] == result["retrieval"]
        with reopened.state.resources.sessions() as session:
            assert len(session.scalars(select(RetrievalSnapshotRecord)).all()) == 1
