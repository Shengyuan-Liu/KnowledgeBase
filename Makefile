.PHONY: test test-live api

api:
	uv run --locked uvicorn knowledgebase.api.app:create_app --factory --host 127.0.0.1 --port 8000

test:
	uv run --locked python -m pytest tests/

test-live:
	RUN_LIVE_API_TESTS=1 uv run --locked python -m pytest tests/test_llm_live.py -s
