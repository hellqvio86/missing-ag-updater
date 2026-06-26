.PHONY: venv lint test clean format build publish run

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
	.venv/bin/mypy src
	.venv/bin/pytest --cov=src/missing_ag_updater --cov-report=term-missing
	.venv/bin/python3 src/generate_badge.py

run: .venv
	.venv/bin/python3 -m missing_ag_updater $(ARGS)

build: .venv
	uv build

publish: build
	uv publish

clean:
	rm -rf .venv __pycache__ .pytest_cache .ruff_cache dist
