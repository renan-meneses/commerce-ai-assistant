# ADR-006: Dead-letter queue and retry policy for indexing

- **Status**: accepted
- **Date**: 2026-08-10

## Context

Transient failures (API down, DB hiccup, embedding provider 5xx) must not poison the indexing queue; permanent failures (malformed event, product deleted) must not retry forever.

## Decision

- The indexing queue declares `x-dead-letter-exchange: commerce.product.dlx`.
- The consumer rejects with `requeue=False` on failure — the message moves to the DLQ; a re-drive script can re-publish it (documented, not yet committed).
- The consumer is idempotent (deterministic chunk ids + delete-before-upsert), so DLQ replay converges.

## Consequences

- Poison messages are visible and replayable, never dropped silently.
- No infinite retry loops in the live queue.
- Cost: DLQ monitoring is an operational duty; alerting on DLQ depth is a documented follow-up.
