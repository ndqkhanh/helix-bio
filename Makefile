.PHONY: help install test lint run docker-up docker-down docker-logs clean

PY ?= python3
VENV ?= .venv
VENV_BIN := $(VENV)/bin
PIP := $(VENV_BIN)/pip
PYTEST := $(VENV_BIN)/pytest
UVICORN := $(VENV_BIN)/uvicorn
PORT ?= 8006

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

$(VENV):
	$(PY) -m venv $(VENV)
	$(PIP) install -U pip wheel

install: $(VENV) ## Install helix-bio + harness_core editable
	$(PIP) install -e ./harness_core
	$(PIP) install -e '.[dev]'

test: install ## Run unit tests
	$(PYTEST) -q tests

run: install ## Start FastAPI on $(PORT)
	$(UVICORN) helix_bio.app:app --reload --port $(PORT)

docker-up: ## Start container stack
	docker compose up -d --build

docker-down: ## Stop container stack
	docker compose down -v

docker-logs: ## Tail container logs
	docker compose logs -f

clean: ## Remove caches and venv
	rm -rf $(VENV) .pytest_cache .ruff_cache .mypy_cache
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true

.DEFAULT_GOAL := help
