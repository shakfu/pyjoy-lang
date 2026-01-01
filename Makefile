.PHONY: all sync repl build test coverage lint format typecheck clean

all: sync

sync:
	@uv sync

repl: sync
	@uv run python -m pyjoy

build: sync
	@uv build

test: sync
	@uv run pytest

coverage: sync
	@uv run pytest --cov=src/pyjoy --cov-report=term-missing

lint:
	@uv run ruff check --fix src/ tests/

format:
	@uv run ruff format src/ tests/

typecheck:
	@uv run ty check src/

clean:
	@rm -rf dist .pytest_cache .coverage htmlcov __pycache__ src/pyjoy/__pycache__ tests/__pycache__
