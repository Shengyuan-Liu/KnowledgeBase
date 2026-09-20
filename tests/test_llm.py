import json

import httpx2
import pytest
from openai import OpenAI
from openai.types.responses import EasyInputMessageParam

from knowledgebase.providers.llm import LLMClient


@pytest.mark.parametrize("model", ["test-model-a", "test-model-b"])
def test_generate_sends_messages_and_returns_text_without_network(model):
    messages: list[EasyInputMessageParam] = [
        {"role": "developer", "content": "Answer using the supplied evidence."},
        {"role": "user", "content": "  What does the café serve?\n"},
    ]
    requests = []

    def handle(request):
        requests.append(request)
        assert request.method == "POST"
        assert request.url.path == "/v1/responses"
        assert json.loads(request.content) == {"model": model, "input": messages}
        return httpx2.Response(
            200,
            json={
                "id": "resp_test",
                "object": "response",
                "created_at": 0,
                "status": "completed",
                "model": model,
                "error": None,
                "incomplete_details": None,
                "instructions": None,
                "metadata": {},
                "parallel_tool_calls": False,
                "tools": [],
                "tool_choice": "auto",
                "output": [
                    {
                        "id": "msg_test",
                        "type": "message",
                        "role": "assistant",
                        "status": "completed",
                        "content": [
                            {
                                "type": "output_text",
                                "text": text,
                                "annotations": [],
                            }
                            for text in ["  Coffee", " and tea. [1]\n"]
                        ],
                    }
                ],
            },
        )

    with OpenAI(
        api_key="test-only-key",
        base_url="https://api.openai.test/v1",
        http_client=httpx2.Client(transport=httpx2.MockTransport(handle)),
    ) as sdk:
        assert LLMClient(sdk, model).generate(messages) == "  Coffee and tea. [1]\n"

    assert len(requests) == 1
