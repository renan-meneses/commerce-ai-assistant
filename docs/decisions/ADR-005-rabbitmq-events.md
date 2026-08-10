# ADR-005: RabbitMQ for async indexing events

- **Status**: accepted
- **Date**: 2026-08-10

## Context

Product changes must reach the vector store, but indexing must not block API transactions or couple the API to the AI service's embedding stack.

## Decision

The API publishes `product.created` / `product.updated` events to RabbitMQ (`commerce.product` topic exchange); the AI service's `worker` process consumes them (`commerce.indexing.product` queue, bound `product.*`), fetches the product from the API, and runs the indexing pipeline. Redis in-memory options were rejected: events must survive process restarts and be replayable (durable queue).

## Consequences

- API latency is independent of embedding/model latency.
- The worker can be scaled independently (QoS prefetch 4).
- Cost: a broker to operate; the API degrades to "publish best-effort with reconnect" while the broker is down (reads/writes still served).
- Idempotent consumers make the queue safe to replay (see ADR-003 chunk-id determinism).
