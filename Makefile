.PHONY: test test-live

test:
	uv run --locked python -m pytest tests/

test-live:
	RUN_LIVE_API_TESTS=1 uv run --locked python -m pytest tests/test_llm_live.py -s
