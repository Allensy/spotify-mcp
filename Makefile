.PHONY: help install install-dev test test-cov lint format clean build publish docs

# Default target
help:
	@echo "Spotify MCP - Development Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install        Install package in production mode"
	@echo "  make install-dev    Install package with development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test           Run tests"
	@echo "  make test-cov       Run tests with coverage"
	@echo "  make lint           Run linters (black, mypy, pylint, ruff)"
	@echo "  make format         Format code with black"
	@echo "  make typecheck      Run type checker (mypy)"
	@echo ""
	@echo "Building:"
	@echo "  make build          Build distribution packages"
	@echo "  make clean          Clean build artifacts"
	@echo "  make publish        Publish to PyPI"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   Build Docker image"
	@echo "  make docker-run     Run Docker container"
	@echo "  make docker-auth    Run OAuth authentication in Docker"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs           Build documentation"
	@echo "  make docs-serve     Serve documentation locally"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev,test,docs]"

# Testing
test:
	pytest

test-cov:
	pytest --cov=spotify_mcp --cov-report=html --cov-report=term

test-unit:
	pytest tests/ -m unit

test-integration:
	pytest tests/ -m integration

# Code Quality
lint:
	@echo "Running black..."
	black --check src/ tests/
	@echo "Running ruff..."
	ruff check src/ tests/
	@echo "Running mypy..."
	mypy src/
	@echo "Running pylint..."
	pylint src/spotify_mcp/

format:
	black src/ tests/
	ruff check --fix src/ tests/

typecheck:
	mypy src/

# Building
build: clean
	python -m build

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf src/*.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

publish: build
	twine upload dist/*

publish-test: build
	twine upload --repository testpypi dist/*

# Docker
docker-build:
	docker build -t spotify-mcp:latest .

docker-run:
	docker run --rm -i \
		-v ${HOME}/.cache/spotify-mcp:/app/.cache \
		-e SPOTIPY_CLIENT_ID \
		-e SPOTIPY_CLIENT_SECRET \
		-e SPOTIPY_REDIRECT_URI \
		-e SPOTIPY_CACHE_PATH \
		spotify-mcp:latest

docker-auth:
	docker run --rm -it \
		-v ${HOME}/.cache/spotify-mcp:/app/.cache \
		-e SPOTIPY_CLIENT_ID \
		-e SPOTIPY_CLIENT_SECRET \
		-e SPOTIPY_REDIRECT_URI=http://localhost:8765/callback \
		-e SPOTIPY_CACHE_PATH=/app/.cache/token \
		spotify-mcp:latest python -u /app/src/spotify_mcp/cli/main.py

# Documentation
docs:
	cd docs && make html

docs-serve:
	cd docs/_build/html && python -m http.server 8000

# Development helpers
validate:
	python tests/test_structure.py

quick-test:
	./quick_test.sh

# Pre-commit
pre-commit:
	pre-commit run --all-files


