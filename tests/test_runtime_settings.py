"""Non-default settings must reach real upload, retrieval, and chat workflows."""

import json
import sys
from unittest.mock import MagicMock, Mock

from fastapi.testclient import TestClient
import pytest

from knowledgebase.config import RetrievalOptions
from knowledgebase import cli
from knowledgebase.api import app as api_module
from knowledgebase.schemas import CitationCheck, ConversationAnswer
from knowledgebase.storage.operations import get_chunks, get_document_source


@pytest.mark.parametrize("streaming", [False, True])
@pytest.mark.parametrize("strategy", ["structural", "character", "parent_child", "semantic"])
def test_api_uses_dotenv_for_upload_retrieval_history_and_models(configured_app, tmp_path, monkeypatch, streaming, strategy):
    app, embeddings, sdk = configured_app
    (tmp_path / ".env").write_text(
        "ANSWER_MODEL=custom-answer\nEMBEDDING_MODEL=custom-embedding\nRESOLVER_MODEL=custom-resolver\n"
        "CHUNK_SIZE=12\nCHUNK_OVERLAP=3\nRETRIEVAL_TOP_K=2\nHISTORY_LIMIT=1\n"
        "OPENAI_BASE_URL=https://provider.test/v1\nOPENAI_TIMEOUT_SECONDS=42\nOPENAI_MAX_RETRIES=1\n"
        f"CHUNKING_STRATEGY={strategy}\nCHUNK_MAX_TOKENS=4\nCHUNK_TOKENIZER=o200k_base\n"
        "PARENT_MAX_TOKENS=8\nEVIDENCE_MAX_TOKENS=96\n"
        "RETRIEVAL_STRATEGY=hybrid\nRETRIEVAL_CANDIDATE_LIMIT=3\nBM25_K1=0.9\nBM25_B=0.4\nRRF_K=10\n"
    )
    sdk.responses.create.side_effect = lambda **kw: Mock(
        output_text="Resolved question" if kw["model"] == "custom-resolver" else "Answer. [1]"
    )
    async_sdk = MagicMock()
    async_sdk.__aenter__.return_value = async_sdk
    async_factory = Mock(return_value=async_sdk)
    monkeypatch.setattr(api_module, "AsyncOpenAI", async_factory)
    streamer = Mock()

    async def stream(messages):
        yield "Answer. [1]"

    streamer.stream = stream
    streaming_factory = Mock(return_value=streamer)
    monkeypatch.setattr(api_module, "StreamingLLMClient", streaming_factory)
    with TestClient(app) as client:
        uploaded = client.post("/api/files", files={"file": ("notes.txt", b"abcdefghijklmnopqrstuvwxyz0123456789")})
        assert uploaded.status_code == 201
        if strategy == "character":
            embeddings.embed_documents.assert_called_once_with([
                "abcdefghijkl", "jklmnopqrstu", "stuvwxyz0123", "123456789",
            ])
        else:
            with app.state.resources.sessions() as session:
                chunks = get_chunks(session, uploaded.json()["file_id"])
                source = get_document_source(session, uploaded.json()["file_id"])
            assert source.text == "abcdefghijklmnopqrstuvwxyz0123456789"
            assert len(chunks) >= 2
            assert all(chunk.max_tokens == 4 and chunk.tokenizer == "o200k_base" for chunk in chunks)
            assert all(chunk.token_count <= 4 for chunk in chunks)
            if strategy == "semantic":
                assert embeddings.embed_documents.call_args.args == ([chunk.text for chunk in chunks],)
                assert source.indexing["strategy"] == "semantic"
            else:
                embeddings.embed_documents.assert_called_once_with([chunk.text for chunk in chunks])

        def ask(question, conversation_id=None):
            body = {"question": question, "conversation_id": conversation_id}
            if streaming:
                response = client.post("/api/chat/stream", json={**body, "request_id": question})
                assert response.status_code == 200
                frames = response.text.strip().split("\n\n")
                assert frames[-1].startswith("event: complete\n")
                return json.loads(frames[-1].split("\ndata: ")[1])
            response = client.post("/api/chat", json=body)
            assert response.status_code == 200
            return response.json()

        first = ask("First question")
        assert len(first["sources"]) == (1 if strategy in ("parent_child", "semantic") else 2)
        assert first["retrieval"]["options"] == RetrievalOptions(packing_strategy="parent_then_child", candidate_limit=3, bm25_k1=0.9, bm25_b=0.4, rrf_k=10).model_dump()
        assert first["retrieval"]["top_k"] == 2
        assert first["retrieval"]["max_tokens"] == 96
        assert first["retrieval"]["tokenizer"] == "o200k_base"
        if strategy in ("parent_child", "semantic"):
            assert first["sources"][0]["parent_id"] == first["sources"][0]["chunk_id"]
            assert len(first["sources"][0]["matched_child_ids"]) == 2
        second = ask("Follow-up", first["conversation_id"])
        assert len(second["sources"]) == len(first["sources"])
        assert second["retrieval_question"] == "Resolved question"
        calls = sdk.responses.create.call_args_list
        resolver = [c for c in calls if c.kwargs["model"] == "custom-resolver"]
        assert len(resolver) == 1
        assert json.loads(resolver[0].kwargs["input"][1]["content"])["history"] == [
            {"role": "assistant", "content": "Answer. [1]"},
        ]
        assert [c.kwargs["model"] for c in calls] == (
            ["custom-resolver"] if streaming else ["custom-answer", "custom-resolver", "custom-answer"]
        )
        api_module.EmbeddingClient.assert_called_once_with(sdk, model="custom-embedding")
        streaming_factory.assert_called_once_with(async_sdk, model="custom-answer")
        expected = dict(api_key="offline-test-key", base_url="https://provider.test/v1", timeout=42, max_retries=1)
        api_module.OpenAI.assert_called_once_with(**expected)
        async_factory.assert_called_once_with(**expected)


@pytest.mark.parametrize("override", [False, True])
def test_cli_uses_settings_and_explicit_arguments_override_them(tmp_path, monkeypatch, override):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test")
    (tmp_path / ".env").write_text(
        "ANSWER_MODEL=file-answer\nEMBEDDING_MODEL=file-embedding\nRESOLVER_MODEL=file-resolver\n"
        "CHUNK_SIZE=12\nCHUNK_OVERLAP=3\nRETRIEVAL_TOP_K=2\nHISTORY_LIMIT=1\n"
        "CHUNKING_STRATEGY=structural\nCHUNK_MAX_TOKENS=17\nCHUNK_TOKENIZER=o200k_base\n"
        "PARENT_MAX_TOKENS=33\nEVIDENCE_MAX_TOKENS=113\n"
        "RETRIEVAL_STRATEGY=vector\nRETRIEVAL_CANDIDATE_LIMIT=7\nBM25_K1=0.9\nBM25_B=0.4\nRRF_K=10\n"
    )
    source = tmp_path / "notes.md"
    source.write_text("Example text")
    sdk = MagicMock()
    sdk.__enter__.return_value = sdk
    monkeypatch.setattr(cli, "OpenAI", Mock(return_value=sdk))
    embeddings = Mock()
    monkeypatch.setattr(cli, "EmbeddingClient", Mock(return_value=embeddings))
    llm, resolver = Mock(), Mock()
    llm_factory = Mock(side_effect=[llm, resolver])
    monkeypatch.setattr(cli, "LLMClient", llm_factory)
    ingest = Mock(return_value="file")
    monkeypatch.setattr(cli, "ingest_file", ingest)
    answer = Mock(return_value=ConversationAnswer(
        answer="Answer", sources=[], citation_check=CitationCheck(valid_source_ids=[], invalid_source_ids=[], no_citations=True),
        conversation_id="conversation", message_id=1, question="Question", retrieval_question="Question",
    ))
    monkeypatch.setattr(cli, "answer_in_conversation", answer)
    monkeypatch.setattr(cli, "run_chat_loop", lambda ask: ask("Question"))
    argv = ["main.py", str(source)]
    if override:
        argv += ["--model", "argument-answer", "--top-k", "4", "--evidence-packing-strategy", "parent_first"]
    monkeypatch.setattr(sys, "argv", argv)
    cli.cli()
    assert llm_factory.call_args_list[0].kwargs["model"] == ("argument-answer" if override else "file-answer")
    assert llm_factory.call_args_list[1].kwargs["model"] == "file-resolver"
    cli.EmbeddingClient.assert_called_once_with(sdk, model="file-embedding")
    assert ingest.call_args.kwargs == {
        "chunk_size": 12, "overlap": 3, "chunking_strategy": "structural",
        "chunk_max_tokens": 17, "chunk_tokenizer": "o200k_base", "parent_max_tokens": 33,
        "semantic_similarity_threshold": 0.5, "semantic_batch_size": 32, "embedding_model": "file-embedding",
    }
    assert answer.call_args.kwargs == {
        "reranker_client": None,
        "conversation_id": None, "top_k": 4 if override else 2, "history_limit": 1, "resolver_client": resolver,
        "evidence_max_tokens": 113, "encoding_name": "o200k_base",
        "retrieval_options": RetrievalOptions(strategy="vector", packing_strategy="parent_first" if override else "parent_then_child", candidate_limit=7, bm25_k1=0.9, bm25_b=0.4, rrf_k=10),
    }


@pytest.mark.parametrize("enabled", [True, False])
def test_cli_rerank_switch_and_model_reach_answer_service(tmp_path, monkeypatch, enabled):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "OPENAI_API_KEY=offline-test\nRERANK_ENABLED=true\nRERANK_MODEL=file-reranker\n"
        "RERANK_CANDIDATE_LIMIT=7\nRERANK_MAX_INPUT_TOKENS=1200\n"
        "RERANK_DEVICE=cpu\nRERANK_BATCH_SIZE=2\nRERANK_MAX_PAIR_TOKENS=333\n"
    )
    sdk = MagicMock()
    sdk.__enter__.return_value = sdk
    monkeypatch.setattr(cli, "OpenAI", Mock(return_value=sdk))
    factory = Mock()
    monkeypatch.setattr(cli, "RerankerClient", factory)
    answer = Mock(return_value=Mock(conversation_id="one"))
    monkeypatch.setattr(cli, "answer_in_conversation", answer)
    monkeypatch.setattr(cli, "run_chat_loop", lambda ask: ask("Question"))
    monkeypatch.setattr(sys, "argv", ["main.py", "--rerank-model", "argument-reranker",
                                      "--rerank" if enabled else "--no-rerank"])
    cli.cli()
    options = answer.call_args.kwargs["retrieval_options"]
    assert options.rerank_enabled is enabled
    assert options.rerank_candidate_limit == 7 and options.rerank_max_input_tokens == 1200
    if enabled:
        factory.assert_called_once_with("argument-reranker", device="cpu", batch_size=2, max_pair_tokens=333)
        assert answer.call_args.kwargs["reranker_client"] is factory.return_value
    else:
        factory.assert_not_called()
        assert answer.call_args.kwargs["reranker_client"] is None
