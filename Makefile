.PHONY: test test-live api frontend test-frontend test-browser

api:
	uv run --locked uvicorn knowledgebase.api.app:create_app --factory --host 127.0.0.1 --port 8000

test:
	uv run --locked python -m pytest tests/

test-live:
	RUN_LIVE_API_TESTS=1 uv run --locked python -m pytest tests/test_llm_live.py -s

frontend:
	npm --prefix frontend run dev

test-frontend:
	npm --prefix frontend test
	npm --prefix frontend run build

test-browser:
	npm --prefix frontend run test:e2e
