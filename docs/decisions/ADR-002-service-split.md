# ADR-002: Split commerce API and AI assistant into separate services

- **Status**: accepted
- **Date**: 2026-08-10

## Context

The assistant needs LLM SDKs, a graph runtime and vector search, while the commerce domain needs Prisma, NestJS middleware and battle-tested HTTP primitives. Mixing both in one process couples release cycles and incident blast radius, and forces the AI stack onto the transactional schema.

## Decision

Two HTTP services plus a worker:

- `apps/api` (NestJS): the commerce backend — catalog, inventory, cart, orders, auth. Owns the relational database via Prisma.
- `apps/ai-service` (FastAPI): the assistant — LangGraph agent, hybrid RAG, evaluation tooling. Owns only `product_embeddings`.
- `worker` (same package as ai-service): consumes indexing events from RabbitMQ.

The AI service **never writes** through the commerce API; it reads via authenticated HTTP and writes only its own vector store.

## Consequences

- Independent scaling: the assistant can burst GPU/LLM traffic without touching transactional capacity.
- The AI service is replaceable without schema churn.
- Cost: cross-service HTTP for tool calls; auth propagation must be designed explicitly (see architecture review).
