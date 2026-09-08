.PHONY: test

test:
	uv run --locked python -m pytest tests/
