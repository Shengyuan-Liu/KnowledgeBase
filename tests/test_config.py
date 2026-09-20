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
