.PHONY: venv lint test clean

.venv: pyproject.toml
	uv venv
	uv pip install pytest ruff

venv: .venv

lint: .venv
	.venv/bin/ruff check .

test: .venv
	.venv/bin/pytest

clean:
	rm -rf .venv __pycache__ .pytest_cache .ruff_cache
