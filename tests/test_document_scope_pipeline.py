"""Exercise actual SQLite/Chroma filtering, shared service paths and snapshots."""

from unittest.mock import Mock

import pytest

from knowledgebase.config import RetrievalOptions
from knowledgebase.providers.llm import LLMClient
from knowledgebase.rag.chunking import DocumentChunker
from knowledgebase.rag.reranking import Reranker
from knowledgebase.rag.retrieval import Retriever
from knowledgebase.services.chat import ChatService
from knowledgebase.services.files import FileService
from knowledgebase.services.rag import RagClient
from knowledgebase.storage.operations import get_conversation_detail


@pytest.fixture
def scope_library(storage, embeddings):
    sessions, store, _ = storage
    # The disallowed file has the stronger lexical match; top-K must be scoped
    # before ranking, not filtered after losing all in-scope candidates.
    g = FileService(sessions, store, embeddings=embeddings).ingest(
        "general-faq.txt", b"Title: General FAQ\n\nAll applicants are considered competitively."
    )
    a = FileService(sessions, store, embeddings=embeddings).ingest(
        "admissions-faq.txt",
        b"Title: Admissions FAQ\n\nScholarships scholarships scholarships. No separate application is needed.",
    )
    embeddings.embed_query.reset_mock()
    return g, a


@pytest.mark.parametrize("strategy", ["vector", "hybrid"])
def test_scope_filters_candidate_search_and_parent_expansion(
    storage, embeddings, scope_library, strategy
):
    sessions, store, _ = storage
    g, a = scope_library
    observed = Mock(wraps=store)
    with sessions() as session:
        result = Retriever(
            embeddings, observed, top_k=1, options=RetrievalOptions(strategy=strategy)
        ).retrieve("According to the general FAQ, how are scholarships awarded?", session)
    assert observed.search.call_args.kwargs["file_ids"] == [g]
    assert {c.file_id for c in result.diagnostics.candidates} == {g}
    assert {c.chunk.file_id for c in result.chunks} == {g}
    assert all("No separate application" not in c.chunk.text for c in result.chunks)
    assert result.diagnostics.document_scope.file_ids == [g]
    assert result.diagnostics.scope_seconds >= 0


@pytest.mark.parametrize(
    "question",
    ["According to the FAQ, how do I apply?", "According to the missing FAQ, how do I apply?"],
)
def test_unresolved_scope_is_saved_clarification_without_provider_calls(
    storage, embeddings, scope_library, question
):
    sessions, store, _ = storage
    llm = Mock(spec=LLMClient)
    result = ChatService(sessions, RagClient(sessions, Retriever(embeddings, store), llm)).answer(
        question
    )
    assert result.sources == [] and result.citation_check.no_citations
    assert "Please specify" in result.answer
    llm.generate.assert_not_called()
    embeddings.embed_query.assert_not_called()
    with sessions() as session:
        saved = get_conversation_detail(session, result.conversation_id).messages[-1]
    assert saved.retrieval.document_scope == result.retrieval.document_scope
    assert saved.content == result.answer


@pytest.mark.anyio
@pytest.mark.parametrize("file_ids_mode", ["automatic", "explicit", "ambiguous", "missing"])
async def test_json_and_streaming_scope_prompt_sources_history_match(
    storage, embeddings, scope_library, file_ids_mode
):
    sessions, store, _ = storage
    g, a = scope_library
    question = "According to the general FAQ, how are applicants considered?"
    ids = None
    if file_ids_mode == "explicit":
        question = "How are applicants considered?"
        ids = [g]
    if file_ids_mode == "ambiguous":
        question = "According to the FAQ, how are applicants considered?"
    if file_ids_mode == "missing":
        ids = ["deleted"]
    llm = Mock(spec=LLMClient)
    llm.generate.return_value = "All applicants are considered competitively. [1]"
    sync = ChatService(sessions, RagClient(sessions, Retriever(embeddings, store), llm)).answer(
        question, file_ids=ids
    )
    captured = []

    class Stream:
        async def stream(self, messages):
            captured.append(messages)
            yield llm.generate.return_value

    iterator = await ChatService(
        sessions, RagClient(sessions, Retriever(embeddings, store), llm, Stream())
    ).stream(question, "request", file_ids=ids)
    events = [e async for e in iterator]
    assert events[-1].event == "complete"
    complete = events[-1].data
    assert sync.answer == complete["answer"]
    assert [s.model_dump(mode="json") for s in sync.sources] == complete["sources"]
    assert sync.retrieval.document_scope.model_dump() == complete["retrieval"]["document_scope"]
    assert "".join(e.data["delta"] for e in events if e.event == "answer_delta") == sync.answer
    if file_ids_mode in {"automatic", "explicit"}:
        assert captured == [llm.generate.call_args.args[0]]
        assert {s.file_id for s in sync.sources} == {g}
        FileService(sessions, store).delete(g)
    else:
        assert captured == []
        llm.generate.assert_not_called()
        embeddings.embed_query.assert_not_called()
    with sessions() as session:
        saved = get_conversation_detail(session, complete["conversation_id"]).messages[-1]
    assert saved.retrieval.document_scope == sync.retrieval.document_scope
    assert all(s.file_deleted for s in saved.sources)


def test_comparison_and_unrestricted_queries_keep_both_documents(
    storage, embeddings, scope_library
):
    sessions, store, _ = storage
    g, a = scope_library
    llm = Mock(spec=LLMClient)
    llm.generate.return_value = "Recorded answer."
    for question in [
        "According to the general FAQ and admissions FAQ, compare scholarships.",
        "How do scholarships work?",
    ]:
        result = RagClient(sessions, Retriever(embeddings, store), llm).answer(question)
        assert {s.file_id for s in result.sources} == {g, a}


def test_original_named_document_cannot_be_widened_by_rewrite(storage, embeddings, scope_library):
    sessions, store, _ = storage
    g, a = scope_library
    llm = Mock(spec=LLMClient)
    llm.generate.return_value = "Recorded answer."
    result = RagClient(sessions, Retriever(embeddings, store), llm).answer(
        "According to the general FAQ, how do I apply?",
        retrieval_question="According to admissions FAQ, how do I apply?",
    )
    assert {s.file_id for s in result.sources} == {g}


def test_followup_retains_resolved_document_clause(storage, embeddings, scope_library):
    sessions, store, _ = storage
    g, a = scope_library
    llm = Mock(spec=LLMClient)
    llm.generate.return_value = "Recorded answer."
    first = ChatService(sessions, RagClient(sessions, Retriever(embeddings, store), llm)).answer(
        "According to general FAQ, who is considered?"
    )
    resolver = Mock(spec=LLMClient)
    resolver.generate.return_value = "According to general FAQ, is there a separate application?"
    result = ChatService(
        sessions, RagClient(sessions, Retriever(embeddings, store), llm), resolver=resolver
    ).answer(
        "What does that page say about a separate application?",
        conversation_id=first.conversation_id,
    )
    assert {s.file_id for s in result.sources} == {g}
    assert "No separate application" not in llm.generate.call_args.args[0][0]["content"]


@pytest.mark.parametrize("endpoint", ["/api/chat", "/api/chat/stream"])
def test_http_explicit_scope_and_missing_file_return_completed_answers(
    configured_app, monkeypatch, endpoint
):
    import json

    from fastapi.testclient import TestClient

    from knowledgebase import bootstrap

    app, _, _ = configured_app
    llm = Mock(spec=LLMClient)
    llm.generate.return_value = "Scoped answer. [1]"

    class Stream:
        async def stream(self, messages):
            yield "Scoped answer. [1]"

    monkeypatch.setattr(bootstrap, "LLMClient", Mock(return_value=llm))
    monkeypatch.setattr(bootstrap, "StreamingLLMClient", Mock(return_value=Stream()))
    with TestClient(app) as client:
        resources = app.state.resources
        g = FileService(
            resources.sessions, resources.store, embeddings=resources.embeddings
        ).ingest("general.txt", b"General facts.")
        FileService(resources.sessions, resources.store, embeddings=resources.embeddings).ingest(
            "other.txt", b"Other facts."
        )
        for ids in ([g], ["deleted"]):
            response = client.post(
                endpoint, json={"question": "What facts?", "request_id": "scope", "file_ids": ids}
            )
            assert response.status_code == 200
            if endpoint.endswith("/stream"):
                frame = response.text.strip().split("\n\n")[-1]
                assert frame.startswith("event: complete\n")
                result = json.loads(frame.split("\ndata: ", 1)[1])
            else:
                result = response.json()
            scope = result["retrieval"]["document_scope"]
            assert scope["file_ids"] == ([g] if ids == [g] else [])
            assert {s["file_id"] for s in result["sources"]} == ({g} if ids == [g] else set())
            history = client.get(f"/api/conversations/{result['conversation_id']}").json()[
                "messages"
            ][-1]
            assert history["retrieval"]["document_scope"] == scope
        assert (
            client.post(
                endpoint, json={"question": "What facts?", "request_id": "scope", "file_ids": []}
            ).status_code
            == 422
        )


@pytest.mark.parametrize(
    "strategy,rerank_enabled", [("vector", False), ("hybrid", False), ("hybrid", True)]
)
def test_one_document_cannot_consume_all_comparison_candidates(
    storage, embeddings, strategy, rerank_enabled
):
    from types import SimpleNamespace

    import tiktoken

    from knowledgebase.rag.context import build_context
    from knowledgebase.schemas import RelevanceScore

    sessions, store, _ = storage
    a = FileService(
        sessions,
        store,
        embeddings=embeddings,
        chunker=DocumentChunker(chunking_strategy="character", chunk_size=40, overlap=0),
    ).ingest("admissions-faq.txt", b"Scholarship application details. " * 35)
    embeddings.embed_documents.side_effect = lambda texts: [[0.0, 1.0] for _ in texts]
    g = FileService(sessions, store, embeddings=embeddings).ingest(
        "general-faq.txt", b"Title: General FAQ\n\nAll applicants are considered."
    )
    reranker = (
        SimpleNamespace(
            model="offline",
            model_revision="test",
            device="cpu",
            max_pair_tokens=512,
            batch_size=4,
            score=lambda question, candidates: [
                RelevanceScore(chunk_id=c.chunk_id, score=0 if "All applicants" in c.text else 3)
                for c in candidates
            ],
        )
        if rerank_enabled
        else None
    )
    observed = Mock(wraps=store)
    with sessions() as session:
        result = Retriever(
            embeddings,
            observed,
            top_k=3,
            options=RetrievalOptions(strategy=strategy, rerank_enabled=rerank_enabled),
            reranker=Reranker(
                reranker,
                candidate_limit=(
                    RetrievalOptions(strategy=strategy, rerank_enabled=rerank_enabled)
                ).rerank_candidate_limit,
                max_input_tokens=(
                    RetrievalOptions(strategy=strategy, rerank_enabled=rerank_enabled)
                ).rerank_max_input_tokens,
            ),
        ).retrieve(
            "According to general FAQ and admissions FAQ, how do scholarships work?", session
        )
    assert {tuple(call.kwargs["file_ids"]) for call in observed.search.call_args_list} == {
        (g,),
        (a,),
    }
    assert len(result.diagnostics.candidates) == 3
    assert {c.file_id for c in result.diagnostics.candidates[:2]} == {g, a}
    assert {c.chunk.file_id for c in result.chunks} == {g, a}
    general = next(c for c in result.chunks if c.chunk.file_id == g)
    assert "General FAQ" in general.document_labels
    context = build_context(result.chunks)
    assert '"document_labels"' in context
    assert (
        len(tiktoken.get_encoding("cl100k_base").encode_ordinary(context))
        == result.diagnostics.evidence_tokens
        <= 4096
    )
    assert result.diagnostics.context_format == "source-metadata-v2"
