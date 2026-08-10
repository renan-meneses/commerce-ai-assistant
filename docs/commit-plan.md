# Commit Plan

> Small, cohesive, reviewable commits. Conventional Commits.
> Commits are created when each unit of work is complete — timestamps are
> never fabricated or backdated.

## Commit 01
`chore: initialize monorepo structure`
- Root folders: apps/api, apps/ai-service, apps/web, packages/, infrastructure/, docs/, evaluation/, scripts/
- .gitignore, .env.example, Makefile
- docs/tasks.md, docs/commit-plan.md

## Commit 02
`chore: add local docker infrastructure`
- docker-compose.yml (postgres+pgvector, redis, rabbitmq)
- infrastructure/postgres/init, healthchecks
- Basic CI wiring

## Commit 03
`feat(api): add nestjs application foundation`
- NestJS app skeleton: health module, config, Swagger, error handling, correlation ID middleware
- Prisma client setup

## Commit 04
`feat(api): add prisma schema and migrations`
- users, categories, products, inventory, carts, cart_items, orders, order_items
- vector extension init for pgvector

## Commit 05
`feat(api): implement products and categories modules`
- Controller/Service/Repository pattern, DTO validation, pagination + filters, Swagger docs
- Unit + e2e tests

## Commit 06
`feat(api): implement inventory and cart modules`
- Availability, reservation-safe operations, cart totals
- Unit + e2e tests

## Commit 07
`feat(api): implement orders module`
- Transactional order creation from cart, status flow, stock decrement
- Unit + e2e tests

## Commit 08
`feat(api): implement auth and users module`
- Register/login, JWT, guards, password hashing
- Unit + e2e tests

## Commit 09
`chore(api): add seed data`
- 20 notebooks, 20 smartphones, 10 monitors, 10 accessories with realistic specs

## Commit 10
`feat(ai): add fastapi foundation and llm abstraction`
- FastAPI app, health, config, OpenTelemetry
- LLMProvider protocol, OpenAI adapter, embedding abstraction, structured output schemas

## Commit 11
`feat(rag): add product document building and chunking`
- Document builder, chunking with deterministic IDs
- Unit tests

## Commit 12
`feat(rag): implement pgvector storage and semantic retrieval`
- Vector upsert layer, parameterized SQL, HNSW index, semantic search with metadata filters

## Commit 13
`feat(rag): implement hybrid search and reranking`
- PostgreSQL FTS + trigram keyword search, fusion (RRF), Reranker protocol + SimpleScoreReranker

## Commit 14
`feat(agent): initialize langgraph workflow`
- AgentState, intent classification, requirements extraction, graph with routing
- Behavioral tests for routing

## Commit 15
`feat(agent): add commerce tools`
- search_products, get_product_details, compare_products, get_product_price, get_inventory, get_user_orders, get_order_status, calculate_shipping
- Tool framework: schema, validation, auth, error handling

## Commit 16
`feat(agent): implement rag + response generation nodes`
- RAG node, response generation, validation node, iteration limits

## Commit 17
`feat(worker): add async product indexing`
- RabbitMQ consumer, document/embed/upsert pipeline, retry + DLQ, idempotency (deterministic doc ids + versioning)
- API publishes product events

## Commit 18
`feat(observability): add langfuse and prometheus tracing`
- Langfuse integration with content masking, Prometheus metrics, correlation IDs

## Commit 19
`feat(security): add prompt injection defenses`
- Injection refusal rules, tool permission model, security tests

## Commit 20
`test(ai): add behavioral and retrieval evaluation`
- evaluation/datasets, evaluation CLI, behavioral tests, retrieval precision/recall

## Commit 21
`docs: add architecture decision records`
- ADR-001 … ADR-008

## Commit 22
`docs: finalize architecture documentation`
- README, architecture.md, rag/agent/system docs, security, observability, ci-cd, testing
- interview-guide.md, architecture-review.md

## Commit 23
`ci: add github actions workflows`
- ci.yml, security.yml, ai-evaluation.yml
- Semgrep config, Docker builds

## Commit 24
`feat(web): add react chat demo client`
- Minimal Vite app with product browsing + AI assistant chat panel

> Commit count may shift as implementation evolves; prefer more small commits.
