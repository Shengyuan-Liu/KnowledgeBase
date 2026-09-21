from pathlib import Path

from knowledgebase.config import Settings


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
    assert Settings().data_dir == Path("data")
    (tmp_path / ".env").write_text("DATA_DIR=custom-data\n", encoding="utf-8")
    assert Settings().data_dir == Path("custom-data")


def test_answer_model_defaults_and_environment_override(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("ANSWER_MODEL", raising=False)
    assert Settings().answer_model == "gpt-4.1-mini"
    monkeypatch.setenv("ANSWER_MODEL", "test-model")
    assert Settings().answer_model == "test-model"
