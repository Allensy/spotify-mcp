.PHONY: help install install-dev test test-cov lint format clean build docs

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

# Docker
spotify_auth_mode = $(or $(strip $(SPOTIFY_AUTH_MODE)),$(if $(strip $(SPOTIPY_CLIENT_SECRET)),legacy,pkce))
spotify_cache_path = $(or $(SPOTIPY_CACHE_PATH),$(if $(filter pkce,$(spotify_auth_mode)),/app/.cache/token-pkce.json,/app/.cache/token))
spotify_redirect = $(or $(SPOTIPY_REDIRECT_URI),http://127.0.0.1:8888/callback)
spotify_callback_port = $(firstword $(subst /, ,$(patsubst http://127.0.0.1:%,%,$(filter http://127.0.0.1:%,$(spotify_redirect)))))
spotify_auto_callback = $(and $(filter pkce,$(spotify_auth_mode)),$(spotify_callback_port))

docker-build:
	docker build -t spotify-mcp:latest .

docker-run:
	docker run --rm -i \
		-v ${HOME}/.cache/spotify-mcp:/app/.cache \
		-e SPOTIPY_CLIENT_ID \
		-e SPOTIPY_CLIENT_SECRET \
		-e SPOTIFY_AUTH_MODE=$(spotify_auth_mode) \
		-e "SPOTIPY_REDIRECT_URI=$(spotify_redirect)" \
		-e "SPOTIPY_CACHE_PATH=$(spotify_cache_path)" \
		spotify-mcp:latest

docker-auth:
	docker run --rm -it \
		$(if $(spotify_auto_callback),-p 127.0.0.1:$(spotify_callback_port):$(spotify_callback_port)) \
		-v ${HOME}/.cache/spotify-mcp:/app/.cache \
		-e SPOTIPY_CLIENT_ID \
		-e SPOTIPY_CLIENT_SECRET \
		-e SPOTIFY_AUTH_MODE=$(spotify_auth_mode) \
		-e "SPOTIPY_REDIRECT_URI=$(spotify_redirect)" \
		-e "SPOTIPY_CACHE_PATH=$(spotify_cache_path)" \
		spotify-mcp:latest python -u -m spotify_mcp.cli.auth_init \
		$(if $(spotify_auto_callback),--no-open --callback-bind 0.0.0.0,--manual)

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


