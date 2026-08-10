# Architecture

## System overview

```
                        ┌──────────────────────────────────────────────┐
                        │                 apps/web (React)             │
                        └───────────┬──────────────────────┬───────────┘
                                    │ HTTP                 │ HTTP
                                    ▼                      ▼
                        ┌───────────────────┐   ┌──────────────────────────────┐
                        │  apps/api         │   │  apps/ai-service             │
                        │  NestJS + Prisma  │──▶│  FastAPI + LangGraph + RAG   │
                        └──┬──────┬─────┬───┘   └───┬────────┬─────────┬───────┘
                           │      │     │           │        │         │
                        PostgreSQL Redis RabbitMQ  PostgreSQL  Redis  Commerce API
                        (+pgvector)  cache  events  (pgvector)  cache  (HTTP tools)
```

## Services

| Service | Stack | Responsibility |
|---|---|---|
| `apps/api` | NestJS 10, Prisma, PostgreSQL, Redis, RabbitMQ | Commerce backend: catalog, inventory, cart, orders, JWT auth, rate limiting, Swagger. Publishes `product.created/updated` events. |
| `apps/ai-service` | FastAPI, LangGraph 1.x, psycopg, pgvector, Redis, httpx | Shopping assistant: intent classification, hybrid retrieval, deterministic tool routing, response generation, evaluations. Consumes indexing events as a separate worker process. |
| `apps/web` | React 18, Vite, react-router | Storefront with product search, cart, orders and an embedded assistant chat widget. |

## Key principles

1. **The AI service never touches the database for writes** — it only reads the vector store it owns and calls the commerce API over HTTP for everything else (ADR-002, ADR-003).
2. **Tools are bounded and read-only** — the tool registry contains only query tools; there are no write tools, so even a successful prompt injection cannot mutate data.
3. **Domain code depends on protocols, not SDKs** — `LLMProvider` and `EmbeddingProvider` are typed Protocols; vendors are adapters (ADR-007).
4. **Determinism where it matters** — intent → tool mapping, chunk ids, and reranking are deterministic; LLM outputs are Pydantic-validated before use.
5. **Idempotent everything** — indexing replays converge (deterministic ids + delete-before-upsert); RabbitMQ consumers tolerate redelivery.
6. **Fail-soft infrastructure** — Redis cache and tracing degrade to no-ops when unavailable; the commerce client retries transient failures.

## Runtime topologies

- **Local dev**: `docker compose up -d postgres redis rabbitmq`, services run from the host (Makefile targets).
- **Full observability**: `docker compose --profile full up -d` adds the OTLP collector, Prometheus, Grafana, and Langfuse.
- **Production-oriented**: services are containerized (`apps/*/Dockerfile`); Prometheus scrapes `/metrics`; traces ship via OTLP to Langfuse.

## Data flow — product indexing

```
api (product saved)
  └─▶ RabbitMQ product.created/updated
       └─▶ worker (ai-service)
            └─▶ fetch product from API
            └─▶ build document → deterministic chunks
            └─▶ embed → upsert pgvector (ON CONFLICT id)
```

## Data flow — assistant chat

```
web ──▶ api/ai/chat ──▶ ai-service POST /api/v1/ai/chat
  analyze (injection scan)
  classify intent ──────────────┐
  extract requirements          │  ┌─ RAG: retrieve (hybrid) → rerank
  route: RAG / TOOLS / REFUSED ─┘  └─ TOOLS: select_tool → execute_tool (auth enforced)
  generate response (validated) ──▶ answer + sources
```

## Commit strategy

One logical change per commit, truthful timestamps, no backdating. See `docs/commit-plan.md`.
