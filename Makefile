# ============================================================
# commerce-ai-assistant — Makefile
# ============================================================

SHELL := /bin/bash
.DEFAULT_GOAL := help

.PHONY: help
help: ## Show available commands
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-24s\033[0m %s\n", $$1, $$2}'

# ---------- Infrastructure ----------

.PHONY: infra-up
infra-up: ## Start core local infrastructure (postgres, redis, rabbitmq)
	docker compose up -d postgres redis rabbitmq

.PHONY: up
up: ## Start full stack (API, AI service, worker, web)
	docker compose up -d --build api ai-service worker web

.PHONY: up-full
up-full: ## Start full stack including observability (prometheus, grafana, langfuse)
	docker compose --profile full up -d --build

.PHONY: down
down: ## Stop all containers
	docker compose down

.PHONY: down-clean
down-clean: ## Stop containers and remove volumes
	docker compose down -v

.PHONY: logs
logs: ## Follow logs for all services
	docker compose logs -f --tail=100

# ---------- Database ----------

.PHONY: db-migrate
db-migrate: ## Run Prisma migrations
	cd apps/api && npx prisma migrate dev

.PHONY: db-deploy
db-deploy: ## Apply migrations to current database (non-interactive)
	cd apps/api && npx prisma migrate deploy

.PHONY: db-seed
db-seed: ## Seed database with demo data
	cd apps/api && npx prisma db seed

.PHONY: db-studio
db-studio: ## Open Prisma Studio
	cd apps/api && npx prisma studio

.PHONY: db-reset
db-reset: ## Reset database, re-apply migrations and seed
	cd apps/api && npx prisma migrate reset --force

# ---------- API (NestJS) ----------

.PHONY: api-install
api-install: ## Install API dependencies
	cd apps/api && yarn install

.PHONY: api-dev
api-dev: ## Run NestJS in watch mode
	cd apps/api && yarn start:dev

.PHONY: api-build
api-build: ## Build NestJS
	cd apps/api && yarn build

.PHONY: api-test
api-test: ## Run API unit tests
	cd apps/api && yarn test

.PHONY: api-test-e2e
api-test-e2e: ## Run API e2e tests
	cd apps/api && yarn test:e2e

# ---------- AI Service (FastAPI) ----------

.PHONY: ai-install
ai-install: ## Create venv and install AI service deps
	cd apps/ai-service && python3.12 -m venv .venv && .venv/bin/pip install -e ".[dev]"

.PHONY: ai-dev
ai-dev: ## Run AI service with hot reload
	cd apps/ai-service && .venv/bin/uvicorn app.main:app --reload --port 8000

.PHONY: ai-test
ai-test: ## Run AI service tests
	cd apps/ai-service && .venv/bin/pytest

# ---------- Quality ----------

.PHONY: lint
lint: ## Lint all workspaces
	cd apps/api && yarn lint && cd ../../apps/ai-service && .venv/bin/ruff check app tests

.PHONY: format
format: ## Format all code
	cd apps/api && yarn format && cd ../../apps/ai-service && .venv/bin/ruff format app tests

.PHONY: types
types: ## Type-check all workspaces
	cd apps/api && yarn build && cd ../../apps/ai-service && .venv/bin/mypy app --ignore-missing-imports

.PHONY: test
test: ## Run all tests (no external LLM calls)
	cd apps/api && yarn test && cd ../../apps/ai-service && .venv/bin/pytest -m "not llm"

.PHONY: security
security: ## Run security scans (semgrep)
	semgrep --config auto apps/api/src apps/ai-service/app --error --exclude-rule=*.lang.raise_debug
	cd apps/api && yarn audit --groups dependencies

.PHONY: quality
quality: lint types test ## Full quality gate

# ---------- AI Evaluation ----------

.PHONY: evaluate-ai
evaluate-ai: ## Run RAG + agent evaluation and generate report
	cd apps/ai-service && .venv/bin/python -m app.evaluation.cli

.PHONY: evaluate-rag
evaluate-rag: ## Run retrieval-only evaluation
	cd apps/ai-service && .venv/bin/python -m app.evaluation.cli --suite rag

.PHONY: evaluate-agent
evaluate-agent: ## Run agent behavioral evaluation
	cd apps/ai-service && .venv/bin/python -m app.evaluation.cli --suite agent

# ---------- Dev utilities ----------

.PHONY: swagger
swagger: ## Open API Swagger (must be running)
	@echo "Open http://localhost:3000/docs in your browser"

.PHONY: reindex
reindex: ## Re-index all products into pgvector
	cd apps/ai-service && .venv/bin/python -m app.rag.indexing.cli --reindex-all
