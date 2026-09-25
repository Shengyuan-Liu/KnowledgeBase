import re
import sys
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from knowledgebase import cli
from knowledgebase.schemas import AnswerSource, ChatAnswer, CitationCheck


def test_cli_and_api_share_storage_configuration(configured_app, tmp_path, monkeypatch):
    app, embeddings, sdk = configured_app
    path = tmp_path / "notes.txt"
    path.write_text("The library closes at 5 PM.")
    monkeypatch.setattr(cli, "OpenAI", Mock(return_value=sdk))
    monkeypatch.setattr(cli, "EmbeddingClient", Mock(return_value=embeddings))
    monkeypatch.setattr(sys, "argv", ["main.py", str(path)])
    monkeypatch.setattr("builtins.input", Mock(return_value="exit"))
    cli.cli()
    with TestClient(app) as client:
        files = client.get("/api/files").json()
        assert len(files) == 1
        assert files[0]["file_name"] == "notes.txt"
        assert files[0]["status"] == "ready"
        sdk.responses.create.return_value = Mock(output_text="5 PM. [1]")
        answer = client.post("/api/chat", json={"question": "When does the library close?"})
        assert answer.status_code == 200
        assert answer.json()["sources"][0]["file_id"] == files[0]["file_id"]
    embeddings.embed_documents.assert_called_once()
    assert sdk.__exit__.call_count == 2


def test_loop_prints_answers_and_chunks_for_multiple_questions(monkeypatch, capsys):
    questions = iter(["  ", "When does the café close?", "When does it open?", "quit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(questions))
    ask = Mock(
        side_effect=[
            ChatAnswer(
                answer="At 5 PM. [1]",
                citation_check=CitationCheck(valid_source_ids=[1], invalid_source_ids=[], no_citations=False),
                sources=[AnswerSource(
                    source_id=1,
                    file_id="file-1",
                    file_name="hours.txt",
                    chunk_id="file-1:0",
                    text="The café closes at 5 PM.\nOpen on weekdays.",
                    distance=0.1,
                )],
            ),
            ChatAnswer(answer="Opening hours are not provided.", sources=[],
                       citation_check=CitationCheck(valid_source_ids=[], invalid_source_ids=[], no_citations=True)),
        ]
    )

    cli.run_chat_loop(ask)

    assert [call.args[0] for call in ask.call_args_list] == [
        "When does the café close?", "When does it open?"
    ]
    output = capsys.readouterr().out
    assert "Answer:\nAt 5 PM. [1]" in output
    assert "[1] hours.txt\nChunk ID: file-1:0" in output
    assert "The café closes at 5 PM.\nOpen on weekdays." in output
    assert "Answer:\nOpening hours are not provided." in output
    assert "Retrieved chunks:\nNone." in output
    assert "valid source IDs: [1]; invalid source IDs: []" in output
    assert "Citation check: no numbered citations found." in output
    assert output.endswith("Goodbye.\n")


@pytest.mark.parametrize("stop", ["exit", " QUIT ", EOFError(), KeyboardInterrupt()])
def test_loop_exits_without_asking_model(monkeypatch, capsys, stop):
    reader = Mock(side_effect=[stop])
    monkeypatch.setattr("builtins.input", reader)
    ask = Mock()

    cli.run_chat_loop(ask)

    ask.assert_not_called()
    assert "Goodbye." in capsys.readouterr().out


@pytest.mark.parametrize("strategy", ["structural", "parent_child"])
@pytest.mark.parametrize("suffix", ["txt", "md"])
def test_cli_indexes_and_reuses_local_data(tmp_path, monkeypatch, capsys, suffix, strategy):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    (tmp_path / ".env").write_text(f"OPENAI_API_KEY=test-only-key\nANSWER_MODEL=test-configured-model\nCHUNKING_STRATEGY={strategy}\n", encoding="utf-8")
    path = tmp_path / f"hours.{suffix}"
    text = ("# Hours\n\n" if suffix == "md" else "") + "The café closes at 5 PM."
    path.write_text(text, encoding="utf-8")
    embeddings = Mock()
    embeddings.embed_documents.return_value = [[1.0, 0.0]]
    embeddings.embed_query.return_value = [1.0, 0.0]
    llm = Mock()
    llm.generate.return_value = "At 5 PM. [1]"
    embedding_class = Mock(return_value=embeddings)
    llm_class = Mock(return_value=llm)
    sdk = Mock()
    sdk.__enter__ = Mock(return_value=sdk)
    sdk.__exit__ = Mock(return_value=False)
    sdk_class = Mock(return_value=sdk)
    monkeypatch.setattr(cli, "OpenAI", sdk_class)
    monkeypatch.setattr(cli, "EmbeddingClient", embedding_class)
    monkeypatch.setattr(cli, "LLMClient", llm_class)

    monkeypatch.setattr(sys, "argv", ["main.py", str(path), "--top-k", "1"])
    monkeypatch.setattr("builtins.input", Mock(side_effect=["When does the café close?", "exit"]))
    cli.cli()

    embeddings.embed_documents.assert_called_once_with([text])
    sdk_class.assert_called_once_with(api_key="test-only-key", base_url=None, timeout=600, max_retries=2)
    llm_class.assert_called_once_with(sdk, model="test-configured-model", reasoning_effort=None)
    output = capsys.readouterr().out
    assert f"Indexed {path.name}" in output
    first_conversation_id = re.search(r"Conversation: ([a-f0-9]+)", output).group(1)
    assert "Answer:\nAt 5 PM. [1]" in output
    assert f"[1] {path.name}" in output
    assert text in output

    assert (tmp_path / "data" / "v1" / "knowledgebase.db").is_file()

    monkeypatch.setattr(sys, "argv", ["main.py", "--top-k", "1"])
    monkeypatch.setattr("builtins.input", Mock(side_effect=["What are the hours?", "exit"]))
    cli.cli()

    embeddings.embed_documents.assert_called_once()
    assert llm.generate.call_count == 2
    output = capsys.readouterr().out
    assert "Indexed" not in output
    assert f"[1] {path.name}" in output
    assert text in output
    assert re.search(r"Conversation: ([a-f0-9]+)", output).group(1) != first_conversation_id

    # Resume persisted history, then keep the same conversation within the loop.
    llm.generate.side_effect = ["When does the café close?", "At 5 PM. [1]"] * 2
    monkeypatch.setattr(sys, "argv", ["main.py", "--conversation-id", first_conversation_id])
    monkeypatch.setattr("builtins.input", Mock(side_effect=["When does it close again?", "And its closing time?", "exit"]))
    cli.cli()
    output = capsys.readouterr().out
    assert output.count(f"Conversation: {first_conversation_id}") == 2
    assert "Retrieval question: When does the café close?" in output
    embeddings.embed_query.assert_called_with("When does the café close?")
    assert llm.generate.call_count == 6
    second_resolution = llm.generate.call_args_list[4].args[0][1]["content"]
    assert "When does it close again?" in second_resolution
    assert "What are the hours?" not in second_resolution
