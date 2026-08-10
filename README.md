# commerce-ai-assistant

A production-oriented AI-powered e-commerce platform.

- **apps/api** — NestJS (TypeScript) commerce backend: catalog, inventory, cart, orders, auth (JWT), RabbitMQ event publishing. PostgreSQL + Prisma.
- **apps/ai-service** — FastAPI + LangGraph shopping assistant: intent routing, hybrid RAG (pgvector + FTS), bounded read-only tools, injection defenses, Langfuse tracing.
- **apps/web** — React 18 + Vite storefront with a chat assistant widget.
- **infrastructure/** — Docker Compose stack (Postgres+pgvector, Redis, RabbitMQ) and observability (OpenTelemetry collector, Prometheus, Grafana, Langfuse).
- **evaluation/** — Retrieval and behavioral evaluation suites with generated reports.

## Quick start

```bash
cp .env.example .env
docker compose up -d postgres redis rabbitmq

cd apps/api
yarn install
yarn prisma generate
yarn prisma migrate deploy
yarn prisma db seed          # 59 products + demo user demo@commerce.ai / demo1234
yarn start:dev               # API on :3000 (Swagger at /docs)

cd ../ai-service
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
export EMBEDDINGS_USE_HASH=true    # offline dev/CI embeddings (no API key)
.venv/bin/python -m app.indexing.cli --reindex-all
.venv/bin/uvicorn app.main:app --port 8000
```

Full stack with observability: `docker compose --profile full up -d` (Grafana :3001, Langfuse :3002).

## Verification

```bash
make test-api test-ai evaluate-ai lint-ai typecheck-ai
```

## Documentation

- [Architecture](docs/architecture.md)
- [RAG pipeline](docs/rag-architecture.md)
- [Agent design](docs/agent-architecture.md)
- [Database design](docs/database-design.md)
- [Security](docs/security.md)
- [Observability](docs/observability.md)
- [Testing strategy](docs/testing-strategy.md)
- [CI/CD](docs/ci-cd.md)
- [Architecture review](docs/architecture-review.md)
- [Interview guide](docs/interview-guide.md)
- [Architecture decision records](docs/decisions/)
