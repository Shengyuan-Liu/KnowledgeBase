"""Exercise the SDK's actual schema request and structured-response parsing."""

import json

import httpx2
import pytest
from openai import OpenAI
from pydantic import ValidationError

from knowledgebase.providers.reranker import RerankerClient


@pytest.mark.parametrize("status,refusal", [("completed", False), ("completed", True), ("incomplete", False)])
def test_structured_scores_and_unsuccessful_responses(status, refusal):
    messages = [{"role": "user", "content": "Exact input"}]
    requests = []

    def handle(request):
        requests.append(request)
        body = json.loads(request.content)
        assert body["model"] == "test-reranker"
        assert body["input"] == messages
        assert body["truncation"] == "disabled"
        assert body["text"]["format"]["type"] == "json_schema"
        assert body["text"]["format"]["strict"] is True
        schema = body["text"]["format"]["schema"]
        assert schema["properties"]["child-1"]["maximum"] == 3
        assert schema["required"] == ["child-1"]
        content = {"type": "refusal", "refusal": "Cannot score."} if refusal else {
            "type": "output_text", "text": json.dumps({"child-1": 3}),
            "annotations": [],
        }
        return httpx2.Response(200, json={
            "id": "resp_test", "object": "response", "created_at": 0,
            "status": status, "model": "test-reranker", "error": None,
            "incomplete_details": {"reason": "max_output_tokens"} if status == "incomplete" else None,
            "instructions": None, "metadata": {}, "parallel_tool_calls": False,
            "tools": [], "tool_choice": "auto",
            "output": [{"id": "msg_test", "type": "message", "role": "assistant",
                        "status": status, "content": [content]}],
        })

    with OpenAI(api_key="offline-test", base_url="https://api.openai.test/v1",
                http_client=httpx2.Client(transport=httpx2.MockTransport(handle))) as sdk:
        client = RerankerClient(sdk, "test-reranker")
        if refusal or status != "completed":
            with pytest.raises(RuntimeError, match="structured relevance scores"):
                client.score(messages, ["child-1"])
        else:
            assert [score.model_dump() for score in client.score(messages, ["child-1"])] == [{"chunk_id": "child-1", "score": 3}]
    assert len(requests) == 1


def test_missing_score_is_rejected_by_sdk_schema_for_the_actual_candidate_ids():
    ids = ["file-a:child:1", "file-b:child:9"]

    def handle(request):
        schema = json.loads(request.content)["text"]["format"]["schema"]
        assert schema["required"] == ids
        assert set(schema["properties"]) == set(ids)
        assert schema["additionalProperties"] is False
        return httpx2.Response(200, json={
            "id": "resp_test", "object": "response", "created_at": 0,
            "status": "completed", "model": "test-reranker", "error": None,
            "incomplete_details": None, "instructions": None, "metadata": {},
            "parallel_tool_calls": False, "tools": [], "tool_choice": "auto",
            "output": [{"id": "msg_test", "type": "message", "role": "assistant",
                        "status": "completed", "content": [{
                            "type": "output_text", "text": json.dumps({ids[0]: 3}), "annotations": [],
                        }]}],
        })

    with OpenAI(api_key="offline-test", base_url="https://api.openai.test/v1",
                http_client=httpx2.Client(transport=httpx2.MockTransport(handle))) as sdk:
        with pytest.raises(ValidationError, match="Field required"):
            RerankerClient(sdk, "test-reranker").score([], ids)
