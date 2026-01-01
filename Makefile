.PHONY: all sync repl build test coverage lint format typecheck clean compile-c run-c

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

# Compile example Joy program to C
compile-c: sync
	@mkdir -p build
	@uv run python -m pyjoy compile tests/examples/demo.joy -o build -n demo
	@echo "Binary: build/demo"

# Compile and run the example
run-c: compile-c
	@echo "--- Running compiled Joy program ---"
	@./build/demo

clean:
	@rm -rf dist build .pytest_cache .coverage htmlcov __pycache__ src/pyjoy/__pycache__ tests/__pycache__
