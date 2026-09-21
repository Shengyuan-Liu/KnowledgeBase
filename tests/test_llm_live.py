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
        base_url=settings.openai_base_url,
        max_retries=settings.eval_max_retries,
        timeout=settings.eval_timeout_seconds,
    ) as sdk:
        answer = LLMClient(sdk, model=settings.answer_model).generate(
            [{"role": "user", "content": "Reply with exactly: API_OK"}]
        )

    print(f"OpenAI response: {answer}")
    assert answer.strip()
