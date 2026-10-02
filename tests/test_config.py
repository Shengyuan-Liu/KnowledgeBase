from pathlib import Path

from knowledgebase.config import Settings


def test_parent_child_is_the_default_and_structural_remains_an_explicit_control(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CHUNKING_STRATEGY", raising=False)
    settings = Settings(openai_api_key="offline-test")
    assert settings.chunking_strategy == "parent_child"
    assert settings.rerank_unit == settings.retrieval_options.rerank_unit == "child"
    assert (settings.chunk_max_tokens, settings.parent_max_tokens, settings.evidence_max_tokens) == (512, 1536, 4096)
    assert Settings(openai_api_key="offline-test", chunking_strategy="structural").chunking_strategy == "structural"


def test_loads_settings_from_dotenv(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    (tmp_path / ".env").write_text("OPENAI_API_KEY=test-file-key\n", encoding="utf-8")

    assert Settings().openai_api_key == "test-file-key"


def test_environment_overrides_dotenv(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("OPENAI_API_KEY=test-file-key\n", encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY", "test-environment-key")

    assert Settings().openai_api_key == "test-environment-key"


def test_data_directory_defaults_and_dotenv_override(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATA_DIR", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    assert Settings().data_dir == Path("data/v1")
    (tmp_path / ".env").write_text("DATA_DIR=custom-data\n", encoding="utf-8")
    assert Settings().data_dir == Path("custom-data")


def test_answer_model_defaults_and_environment_override(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("ANSWER_MODEL", raising=False)
    assert Settings().answer_model == "gpt-4.1"
    monkeypatch.setenv("ANSWER_MODEL", "test-model")
    assert Settings().answer_model == "test-model"


def test_calibrated_judge_reasoning_default_and_override(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("JUDGE_REASONING_EFFORT", raising=False)
    assert Settings(openai_api_key="offline-test").judge_reasoning_effort == "high"
    monkeypatch.setenv("JUDGE_REASONING_EFFORT", "medium")
    assert Settings(openai_api_key="offline-test").judge_reasoning_effort == "medium"


def test_all_runtime_options_and_override_precedence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    values = {
        "OPENAI_API_KEY": "test-secret", "OPENAI_BASE_URL": "https://provider.test/v1",
        "OPENAI_TIMEOUT_SECONDS": "42", "OPENAI_MAX_RETRIES": "1", "DATA_DIR": "custom-data",
        "ANSWER_MODEL": "file-answer", "EMBEDDING_MODEL": "file-embedding",
        "RERANK_MODEL": "file-reranker", "RERANK_CANDIDATE_LIMIT": "12", "RERANK_MAX_INPUT_TOKENS": "8000",
        "RERANK_UNIT": "parent",
        "RESOLVER_MODEL": "file-resolver", "CHUNKING_STRATEGY": "character", "CHUNK_MAX_TOKENS": "64",
        "PARENT_MAX_TOKENS": "128", "EVIDENCE_MAX_TOKENS": "256",
        "CHUNK_TOKENIZER": "cl100k_base", "CHUNK_SIZE": "100", "CHUNK_OVERLAP": "20",
        "RETRIEVAL_TOP_K": "3", "HISTORY_LIMIT": "4", "EVAL_TIMEOUT_SECONDS": "12",
        "EVAL_MAX_RETRIES": "0", "JUDGE_MODEL": "file-judge", "JUDGE_TIMEOUT_SECONDS": "180", "JUDGE_REASONING_EFFORT": "high", "JUDGE_CONCURRENCY": "2",
    }
    for key in values:
        monkeypatch.delenv(key, raising=False)
    (tmp_path / ".env").write_text("\n".join(f"{k}={v}" for k, v in values.items()))
    settings = Settings()
    assert settings.retrieval_options.rerank_unit == "parent"
    for key, value in values.items():
        assert str(getattr(settings, key.lower())) == (str(float(value)) if "TIMEOUT" in key else value)
    monkeypatch.setenv("ANSWER_MODEL", "environment-answer")
    assert Settings().answer_model == "environment-answer"
    assert Settings(answer_model="argument-answer").answer_model == "argument-answer"
    assert "test-secret" not in repr(settings)


def test_blank_optional_settings_use_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    for key in ("RESOLVER_MODEL", "OPENAI_BASE_URL", "CHUNK_SIZE", "CHUNK_OVERLAP"):
        monkeypatch.delenv(key, raising=False)
    (tmp_path / ".env").write_text("RESOLVER_MODEL=\nOPENAI_BASE_URL=\nCHUNK_SIZE=\nCHUNK_OVERLAP=\n")
    settings = Settings()
    assert settings.resolver_model is None
    assert settings.answer_reasoning_effort is None
    assert settings.openai_base_url is None
    assert settings.chunk_size == 2048
    assert settings.chunk_overlap == 256


def test_invalid_tuning_values_fail_before_startup_without_exposing_key(tmp_path, monkeypatch):
    import pytest
    from pydantic import ValidationError

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-appear-in-errors")
    for invalid in (
        {"rerank_enabled": True, "retrieval_strategy": "vector"},
        {"rerank_candidate_limit": 0}, {"rerank_max_input_tokens": 0},
        {"rerank_batch_size": 0}, {"rerank_max_pair_tokens": 0}, {"rerank_device": "unknown"},
        {"parent_max_tokens": 0}, {"evidence_max_tokens": 0},
        {"chunking_strategy": "parent_child", "parent_max_tokens": 128, "chunk_max_tokens": 256},
        {"chunking_strategy": "parent_child", "parent_max_tokens": 512, "evidence_max_tokens": 512},
        {"chunk_max_tokens": 0}, {"chunking_strategy": "unknown"},
        {"chunk_size": 0}, {"chunk_overlap": -1},
        {"chunking_strategy": "character", "chunk_size": 16, "chunk_overlap": 16},
        {"retrieval_candidate_limit": 0}, {"retrieval_strategy": "unknown"},
        {"bm25_k1": -1}, {"bm25_b": 1.1}, {"rrf_k": float("inf")},
        {"retrieval_top_k": 0}, {"history_limit": 0}, {"openai_timeout_seconds": 0},
        {"openai_max_retries": -1}, {"eval_timeout_seconds": 0}, {"eval_max_retries": -1},
    ):
        with pytest.raises(ValidationError) as error:
            Settings(**invalid)
        assert "must-not-appear-in-errors" not in str(error.value)


def test_hybrid_is_default_and_vector_is_an_explicit_control(tmp_path, monkeypatch):
    from knowledgebase.schemas.options import RetrievalOptions

    monkeypatch.chdir(tmp_path)
    settings = Settings(openai_api_key="offline-test")
    assert settings.retrieval_options == RetrievalOptions(packing_strategy="parent_then_child")
    assert settings.retrieval_options.strategy == "hybrid"
    assert settings.retrieval_options.candidate_limit == 20
    assert Settings(openai_api_key="offline-test", retrieval_strategy="vector").retrieval_options.strategy == "vector"


def test_rerank_remains_an_explicit_opt_in(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    settings = Settings(openai_api_key="offline-test")
    assert settings.rerank_enabled is False
    assert settings.retrieval_options.rerank_enabled is False
    assert settings.rerank_model == "BAAI/bge-reranker-v2-m3"
    assert settings.rerank_candidate_limit == 20
    assert settings.rerank_max_input_tokens == 16384
    assert settings.retrieval_options.strategy == "hybrid"


def test_answer_reasoning_effort_from_env_and_explicit_override(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ANSWER_REASONING_EFFORT", raising=False)
    (tmp_path / ".env").write_text("OPENAI_API_KEY=offline-test\nANSWER_REASONING_EFFORT=low\n")
    assert Settings().answer_reasoning_effort == "low"
    assert Settings(answer_reasoning_effort="high").answer_reasoning_effort == "high"
