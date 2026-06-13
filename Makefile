.PHONY: venv lint test clean

.venv: pyproject.toml
	uv venv
	uv pip install -e . --group dev

venv: .venv

lint: .venv
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .

format: .venv
	.venv/bin/ruff format .

test: .venv
	.venv/bin/pytest

clean:
	rm -rf .venv __pycache__ .pytest_cache .ruff_cache
