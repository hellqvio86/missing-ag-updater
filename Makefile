.PHONY: venv lint test clean format build publish

.venv: pyproject.toml
	if [ ! -d .venv ]; then uv venv; fi
	uv pip install -e . --group dev

venv: .venv

lint: .venv
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .

format: .venv
	.venv/bin/ruff format .

test: .venv
	.venv/bin/pytest

build: .venv
	uv build

publish: build
	uv publish

clean:
	rm -rf .venv __pycache__ .pytest_cache .ruff_cache dist
