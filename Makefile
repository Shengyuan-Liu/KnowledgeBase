.PHONY: test test-live api frontend test-frontend test-browser test-browser-live stop test-stop

STOP_PORTS ?= 8000 5173 8001 5174 4173

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

test-browser-live:
	npm --prefix frontend run test:live

stop:
	@list_pids() { \
		for port in $(STOP_PORTS); do lsof -tiTCP:$$port -sTCP:LISTEN; done 2>/dev/null | sort -u; \
	}; \
	pids=$$(list_pids); \
	if [ -z "$$pids" ]; then echo "Project ports are already free."; exit 0; fi; \
	echo "Stopping listeners on ports: $(STOP_PORTS)"; \
	kill $$pids || exit 1; \
	for attempt in 1 2 3 4 5; do \
		if [ -z "$$(list_pids)" ]; then echo "Project ports are free."; exit 0; fi; \
		sleep 1; \
	done; \
	echo "Some project ports are still occupied. Check the running processes." >&2; \
	exit 1

test-stop:
	node --test tests/test_stop.mjs
