"""Opt-in test that sends one real request to OpenAI using .env credentials."""

import os

import pytest
from openai import OpenAI

from knowledgebase.config import Settings
from knowledgebase.providers.llm import LLMClient


@pytest.mark.skipif(
    os.environ.get("RUN_LIVE_API_TESTS") != "1",
    reason="Run make test-live to enable real OpenAI API requests.",
)
def test_generate_with_real_openai_api():
    settings = Settings()
    with OpenAI(
        api_key=settings.openai_api_key,
        max_retries=0,
        timeout=30.0,
    ) as sdk:
        answer = LLMClient(sdk, model="gpt-4.1-nano").generate(
            [{"role": "user", "content": "Reply with exactly: API_OK"}]
        )

    print(f"OpenAI response: {answer}")
    assert answer.strip()
