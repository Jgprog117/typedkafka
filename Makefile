.PHONY: install test lint typecheck check build clean

install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy src --ignore-missing-imports

check: lint typecheck test

build: clean
	python -m build
	twine check dist/*

clean:
	rm -rf dist/ build/ *.egg-info htmlcov/ .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
