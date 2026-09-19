from unittest.mock import Mock

import pytest
from openai import OpenAI
from openai.types import CreateEmbeddingResponse

from knowledgebase.providers.embeddings import EmbeddingClient


def response_for(rows):
    return CreateEmbeddingResponse(
        data=[
            {"object": "embedding", "index": index, "embedding": vector}
            for index, vector in rows
        ],
        model="text-embedding-3-small",
        object="list",
        usage={"prompt_tokens": 2, "total_tokens": 2},
    )


@pytest.fixture
def sdk():
    return Mock()


def test_documents_extract_vectors_and_preserve_text(sdk):
    sdk.embeddings.create.return_value = response_for(
        [(0, [0.1, 0.2]), (1, [0.3, 0.4])]
    )
    texts = ["  First\nchunk. ", "Second chunk: café."]

    assert EmbeddingClient(sdk).embed_documents(texts) == [[0.1, 0.2], [0.3, 0.4]]
    sdk.embeddings.create.assert_called_once_with(
        model="text-embedding-3-small", input=texts, encoding_format="float"
    )


def test_query_and_documents_share_configured_model(sdk):
    sdk.embeddings.create.return_value = response_for([(0, [0.1, 0.2])])
    embeddings = EmbeddingClient(sdk, model="text-embedding-3-large")

    documents = embeddings.embed_documents(["A fact."])
    query = embeddings.embed_query("A question?")

    assert query == documents[0]
    assert [call.kwargs["model"] for call in sdk.embeddings.create.call_args_list] == [
        "text-embedding-3-large", "text-embedding-3-large"
    ]
    assert sdk.embeddings.create.call_args.kwargs["input"] == ["A question?"]


def test_provider_failure_propagates_unchanged(sdk):
    failure = RuntimeError("Provider unavailable")
    sdk.embeddings.create.side_effect = failure

    with pytest.raises(RuntimeError) as caught:
        EmbeddingClient(sdk).embed_query("Question?")

    assert caught.value is failure


def test_real_sdk_request_and_response_without_network():
    import json

    import httpx2

    def handle(request):
        assert request.url.path == "/v1/embeddings"
        assert json.loads(request.content) == {
            "model": "text-embedding-3-small",
            "input": ["Example text."],
            "encoding_format": "float",
        }
        return httpx2.Response(
            200, json=response_for([(0, [0.1, 0.2])]).model_dump()
        )

    with OpenAI(
        api_key="test-only-key",
        base_url="https://api.openai.test/v1",
        http_client=httpx2.Client(transport=httpx2.MockTransport(handle)),
    ) as sdk:
        assert EmbeddingClient(sdk).embed_query("Example text.") == [0.1, 0.2]
