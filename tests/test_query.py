import json
from datetime import datetime
from unittest.mock import Mock

from knowledgebase.providers.llm import LLMClient
from knowledgebase.rag.query import resolve_question
from knowledgebase.schemas import MessageInfo


def test_no_history_preserves_original_question_without_model_call():
    llm = Mock(spec=LLMClient)
    question = "  How many credits does NYU MSDS require?\n"
    assert resolve_question(question, [], llm) == question
    llm.generate.assert_not_called()


def test_resolution_passes_ordered_history_as_data_and_returns_retrieval_question():
    history = [
        MessageInfo(message_id=1, conversation_id="chat-1", role="user",
                    content="Tell me about NYU MSDS.", created_at=datetime(2026, 1, 1)),
        MessageInfo(message_id=2, conversation_id="chat-1", role="assistant",
                    content="It is a master's program.", created_at=datetime(2026, 1, 1)),
    ]
    llm = Mock(spec=LLMClient)
    llm.generate.return_value = "How many credits does NYU MSDS require?\n"
    assert resolve_question("How many credits does it require?", history, llm) == "How many credits does NYU MSDS require?"
    llm.generate.assert_called_once()
    instructions, request = llm.generate.call_args.args[0]
    payload = json.loads(request["content"])
    assert payload == {"history": [{"role": m.role, "content": m.content} for m in history],
                       "question": "How many credits does it require?"}
    assert instructions["role"] == "developer"
    assert "Do not answer the question" in instructions["content"]
    assert "instead of guessing" in instructions["content"]
    assert "not factual evidence" in instructions["content"]
