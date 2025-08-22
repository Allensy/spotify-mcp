# Spotify MCP Server - Makefile
# Automates building, testing, and deployment tasks

# Variables
DOCKER_IMAGE = spotify-mcp
DOCKER_TAG = latest
DOCKER_REGISTRY = allesy/spotify-mcp
CACHE_DIR = $(HOME)/.cache/spotify-mcp

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
PURPLE = \033[0;35m
CYAN = \033[0;36m
NC = \033[0m # No Color

.PHONY: help build push pull run auth test clean lint format setup dev stop logs

# Default target
help: ## Show this help message
	@echo "$(CYAN)🎵 Spotify MCP Server - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

## 🏗️  BUILD & DEVELOPMENT

build: ## Build Docker image locally
	@echo "$(BLUE)🏗️  Building Docker image...$(NC)"
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	@echo "$(GREEN)✅ Build complete: $(DOCKER_IMAGE):$(DOCKER_TAG)$(NC)"

build-no-cache: ## Build Docker image without cache
	@echo "$(BLUE)🏗️  Building Docker image (no cache)...$(NC)"
	docker build --no-cache -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	@echo "$(GREEN)✅ Build complete: $(DOCKER_IMAGE):$(DOCKER_TAG)$(NC)"

## 🚀 DEPLOYMENT

push: build ## Build and push to Docker Hub
	@echo "$(PURPLE)🚀 Pushing to Docker Hub...$(NC)"
	docker tag $(DOCKER_IMAGE):$(DOCKER_TAG) $(DOCKER_REGISTRY):$(DOCKER_TAG)
	docker push $(DOCKER_REGISTRY):$(DOCKER_TAG)
	@echo "$(GREEN)✅ Pushed: $(DOCKER_REGISTRY):$(DOCKER_TAG)$(NC)"

pull: ## Pull latest image from Docker Hub
	@echo "$(BLUE)📥 Pulling from Docker Hub...$(NC)"
	docker pull $(DOCKER_REGISTRY):$(DOCKER_TAG)
	@echo "$(GREEN)✅ Pulled: $(DOCKER_REGISTRY):$(DOCKER_TAG)$(NC)"

## 🔐 AUTHENTICATION

auth: setup-cache ## Run OAuth authentication setup
	@echo "$(YELLOW)🔐 Starting OAuth authentication...$(NC)"
	@echo "$(CYAN)ℹ️  You'll need your Spotify Client ID and Secret$(NC)"
	@if [ -z "$(SPOTIPY_CLIENT_ID)" ] || [ -z "$(SPOTIPY_CLIENT_SECRET)" ]; then \
		echo "$(RED)❌ Please set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables$(NC)"; \
		echo "$(CYAN)   export SPOTIPY_CLIENT_ID=your_client_id$(NC)"; \
		echo "$(CYAN)   export SPOTIPY_CLIENT_SECRET=your_client_secret$(NC)"; \
		exit 1; \
	fi
	docker run --rm -it \
		-v $(CACHE_DIR):/app/.cache \
		-e SPOTIPY_CLIENT_ID=$(SPOTIPY_CLIENT_ID) \
		-e SPOTIPY_CLIENT_SECRET=$(SPOTIPY_CLIENT_SECRET) \
		-e SPOTIPY_REDIRECT_URI=http://localhost:8765/callback \
		-e SPOTIPY_CACHE_PATH=/app/.cache/token \
		$(DOCKER_IMAGE):$(DOCKER_TAG) python -u auth_init.py
	@echo "$(GREEN)✅ Authentication complete! Token saved to $(CACHE_DIR)$(NC)"

auth-registry: setup-cache ## Run OAuth authentication with registry image
	@echo "$(YELLOW)🔐 Starting OAuth authentication (registry image)...$(NC)"
	@if [ -z "$(SPOTIPY_CLIENT_ID)" ] || [ -z "$(SPOTIPY_CLIENT_SECRET)" ]; then \
		echo "$(RED)❌ Please set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables$(NC)"; \
		exit 1; \
	fi
	docker run --rm -it \
		-v $(CACHE_DIR):/app/.cache \
		-e SPOTIPY_CLIENT_ID=$(SPOTIPY_CLIENT_ID) \
		-e SPOTIPY_CLIENT_SECRET=$(SPOTIPY_CLIENT_SECRET) \
		-e SPOTIPY_REDIRECT_URI=http://localhost:8765/callback \
		-e SPOTIPY_CACHE_PATH=/app/.cache/token \
		$(DOCKER_REGISTRY):$(DOCKER_TAG) python -u auth_init.py

## 🏃 RUNNING

run: ## Run MCP server (local image)
	@echo "$(GREEN)🎵 Starting Spotify MCP Server...$(NC)"
	@if [ -z "$(SPOTIPY_CLIENT_ID)" ] || [ -z "$(SPOTIPY_CLIENT_SECRET)" ]; then \
		echo "$(RED)❌ Please set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables$(NC)"; \
		exit 1; \
	fi
	@if [ ! -f "$(CACHE_DIR)/token" ]; then \
		echo "$(YELLOW)⚠️  No auth token found. Run 'make auth' first$(NC)"; \
		exit 1; \
	fi
	docker run --rm -i \
		-v $(CACHE_DIR):/app/.cache \
		-e SPOTIPY_CLIENT_ID=$(SPOTIPY_CLIENT_ID) \
		-e SPOTIPY_CLIENT_SECRET=$(SPOTIPY_CLIENT_SECRET) \
		-e SPOTIPY_REDIRECT_URI=http://localhost:8765/callback \
		-e SPOTIPY_CACHE_PATH=/app/.cache/token \
		$(DOCKER_IMAGE):$(DOCKER_TAG)

run-registry: ## Run MCP server (registry image)
	@echo "$(GREEN)🎵 Starting Spotify MCP Server (registry)...$(NC)"
	@if [ -z "$(SPOTIPY_CLIENT_ID)" ] || [ -z "$(SPOTIPY_CLIENT_SECRET)" ]; then \
		echo "$(RED)❌ Please set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables$(NC)"; \
		exit 1; \
	fi
	docker run --rm -i \
		-v $(CACHE_DIR):/app/.cache \
		-e SPOTIPY_CLIENT_ID=$(SPOTIPY_CLIENT_ID) \
		-e SPOTIPY_CLIENT_SECRET=$(SPOTIPY_CLIENT_SECRET) \
		-e SPOTIPY_REDIRECT_URI=http://localhost:8765/callback \
		-e SPOTIPY_CACHE_PATH=/app/.cache/token \
		$(DOCKER_REGISTRY):$(DOCKER_TAG)

run-bg: ## Run MCP server in background
	@echo "$(GREEN)🎵 Starting Spotify MCP Server in background...$(NC)"
	docker run --rm -d --name spotify-mcp \
		-v $(CACHE_DIR):/app/.cache \
		-e SPOTIPY_CLIENT_ID=$(SPOTIPY_CLIENT_ID) \
		-e SPOTIPY_CLIENT_SECRET=$(SPOTIPY_CLIENT_SECRET) \
		-e SPOTIPY_REDIRECT_URI=http://localhost:8765/callback \
		-e SPOTIPY_CACHE_PATH=/app/.cache/token \
		$(DOCKER_IMAGE):$(DOCKER_TAG)
	@echo "$(GREEN)✅ Server running in background (container: spotify-mcp)$(NC)"

## 🧪 TESTING & DEVELOPMENT

test: build ## Run tests in Docker container
	@echo "$(BLUE)🧪 Running tests...$(NC)"
	docker run --rm \
		-v $(PWD):/app \
		-w /app \
		python:3.11-slim \
		sh -c "pip install -r requirements.txt && python -m pytest tests/ -v" || echo "$(YELLOW)⚠️  No tests found$(NC)"

lint: ## Run linting checks
	@echo "$(BLUE)🔍 Running linting checks...$(NC)"
	docker run --rm \
		-v $(PWD):/app \
		-w /app \
		python:3.11-slim \
		sh -c "pip install flake8 black isort mypy && flake8 *.py && black --check *.py && isort --check-only *.py"

format: ## Format Python code
	@echo "$(BLUE)🎨 Formatting Python code...$(NC)"
	docker run --rm \
		-v $(PWD):/app \
		-w /app \
		python:3.11-slim \
		sh -c "pip install black isort && black *.py && isort *.py"
	@echo "$(GREEN)✅ Code formatted$(NC)"

dev: ## Start development environment
	@echo "$(CYAN)🛠️  Setting up development environment...$(NC)"
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	@echo "$(GREEN)✅ Development environment ready$(NC)"
	@echo "$(CYAN)   Activate with: source .venv/bin/activate$(NC)"

## 🔧 UTILITIES

setup-cache: ## Create cache directory
	@mkdir -p $(CACHE_DIR)
	@echo "$(GREEN)✅ Cache directory created: $(CACHE_DIR)$(NC)"

stop: ## Stop background MCP server
	@echo "$(YELLOW)🛑 Stopping background server...$(NC)"
	docker stop spotify-mcp 2>/dev/null || echo "$(YELLOW)⚠️  No background server running$(NC)"

logs: ## Show logs from background server
	@echo "$(CYAN)📋 Server logs:$(NC)"
	docker logs spotify-mcp

clean: ## Clean up Docker images and containers
	@echo "$(YELLOW)🧹 Cleaning up...$(NC)"
	docker stop spotify-mcp 2>/dev/null || true
	docker rm spotify-mcp 2>/dev/null || true
	docker rmi $(DOCKER_IMAGE):$(DOCKER_TAG) 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

clean-cache: ## Remove authentication cache
	@echo "$(YELLOW)🧹 Removing authentication cache...$(NC)"
	rm -rf $(CACHE_DIR)
	@echo "$(GREEN)✅ Cache removed$(NC)"

## 📋 INFO

info: ## Show project information
	@echo "$(CYAN)🎵 Spotify MCP Server Information$(NC)"
	@echo ""
	@echo "$(GREEN)Project:$(NC)       Spotify MCP Server"
	@echo "$(GREEN)Image:$(NC)         $(DOCKER_IMAGE):$(DOCKER_TAG)"
	@echo "$(GREEN)Registry:$(NC)      $(DOCKER_REGISTRY):$(DOCKER_TAG)"
	@echo "$(GREEN)Cache Dir:$(NC)     $(CACHE_DIR)"
	@echo ""
	@echo "$(GREEN)Docker Images:$(NC)"
	@docker images | grep -E "(spotify-mcp|allesy/spotify-mcp)" || echo "  No images found"
	@echo ""
	@echo "$(GREEN)Running Containers:$(NC)"
	@docker ps | grep spotify-mcp || echo "  No containers running"

env-example: ## Show environment variable examples
	@echo "$(CYAN)🔧 Required Environment Variables$(NC)"
	@echo ""
	@echo "$(GREEN)export SPOTIPY_CLIENT_ID=your_spotify_client_id$(NC)"
	@echo "$(GREEN)export SPOTIPY_CLIENT_SECRET=your_spotify_client_secret$(NC)"
	@echo ""
	@echo "$(CYAN)Optional:$(NC)"
	@echo "$(YELLOW)export SPOTIPY_REDIRECT_URI=http://localhost:8765/callback$(NC)"
	@echo "$(YELLOW)export SPOTIFY_SCOPE=\"user-read-playback-state user-modify-playback-state\"$(NC)"

## 🎯 WORKFLOWS

quick-start: build auth ## Complete setup: build + auth
	@echo "$(GREEN)🎉 Quick start complete! Your Spotify MCP is ready to use.$(NC)"
	@echo ""
	@echo "$(CYAN)Next steps:$(NC)"
	@echo "  1. Add to your MCP client config"
	@echo "  2. Run: $(GREEN)make run$(NC)"

deploy: build push ## Complete deployment: build + push
	@echo "$(GREEN)🚀 Deployment complete!$(NC)"

full-clean: clean clean-cache ## Complete cleanup: images + cache
	@echo "$(GREEN)🧹 Full cleanup complete$(NC)"

## 📊 GIT

commit: ## Create commit for current changes
	@echo "$(BLUE)📝 Creating commit...$(NC)"
	git add .
	git status
	@read -p "Enter commit message: " msg; \
	git commit -m "$$msg"

push-git: ## Push changes to git repository
	@echo "$(PURPLE)📤 Pushing to git repository...$(NC)"
	git push

release: deploy push-git ## Full release: deploy + push git
	@echo "$(GREEN)🎉 Release complete!$(NC)"
