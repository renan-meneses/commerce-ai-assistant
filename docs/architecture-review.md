# Architecture Review

Honest self-review of `commerce-ai-assistant` as of the last commit. Written to be useful to a reviewer — strengths first, then the things that would not survive production without work.

## What is strong

1. **Trust boundary is explicit and enforced.** The LLM can only call read-only bounded tools; auth-required tools are enforced in `execute_tool`, not promised by the model; injection-flagged input is refused before any LLM call. This is the difference between "demo agent" and "defensible agent".
2. **Determinism where the model is weak.** Intent→tool mapping, chunk ids, fusion and reranking are deterministic. Evaluations run without a model and without keys, and they test the actual graph (`ScriptedLLMProvider` + stubbed I/O).
3. **Idempotent data pipeline.** Replayed RabbitMQ events and re-runs of `--reindex-all` converge; chunk-id hashing + delete-before-upsert makes this cheap to reason about.
4. **Repository pattern in the API.** Domain services depend on interfaces (`PRODUCT_REPOSITORY`, …) — testable, and the Prisma leak is contained.
5. **Honest evaluations.** The RAG dataset was rewritten to match the real seeded catalog (pt-BR); feature matching is token-based; pass bars are explicit (recall ≥0.8, category ≥0.8, feature ≥0.6; behavioral 100%).

## Known gaps (would block production as-is)

1. **~~AI-service auth propagation~~ (FIXED).** The API now mints a short-lived scoped JWT
   (`aud=ai-service`, 5 min) and forwards it as `x-service-token`; tools forward it to the
   commerce API as Bearer, so the backend enforces ownership on user-scoped endpoints.
   Security gate and tools check token presence (tests cover minting + forwarding).
2. **No model quality gate in CI.** Evaluations measure routing/retrieval/security behavior, not answer quality. A golden-answer eval with a real model (weekly, keyed) is missing.
3. **~~Rate limiting asymmetry~~ (FIXED).** The AI service now enforces its own Redis-backed
   fixed-window limiter on `/api/v1/ai/chat` (30 req/60s, stricter than the API's 60, since the
   agent path is LLM-bound), fail-open when Redis is down.
4. **Hash embeddings are not semantic.** `EMBEDDINGS_USE_HASH=true` is for CI only; production needs OpenAI or local bge plus a reindex. Nothing in code prevents it accidentally being enabled in prod (documented, not enforced).
5. **DLQ re-drive script is documented but not committed.** A failure loop would accumulate messages without an operational escape hatch.
6. **Web app is a reference client.** No tests, no auth token refresh, no error UX polish. Fine as a showcase; not production-ready by itself.
7. **No secrets rotation / no KMS.** JWT secret and RabbitMQ creds are env placeholders; fine for dev, needs a real secrets story.
8. **Prisma migration owns the vector DDL.** The API's migration creates `product_embeddings`; the AI service owns all queries. It works, but a schema change requires touching both pipelines — the ownership boundary is documented in ADR-003.

## Design decisions I would defend

- **Two services** (ADR-002): LLM traffic should never compete with transactional capacity.
- **pgvector over a vector DB**: single database for a small catalog; HNSW + metadata filters are plenty; the AI service can later move to a dedicated vector DB without changing the API.
- **Deterministic intent→tool mapping over LLM tool-calling**: simpler to secure, cheaper, and the intent space is small enough that the cheap classifier is sufficient.
- **OR-term keyword search with stopword filtering**: AND semantics made comparison queries unanswerable (found by the eval); OR + `ts_rank` + fusion ordering keeps precision in practice (validated: 10/10 with hash embeddings).

## Metrics to watch in production

- DLQ depth; indexing lag (event→chunk latency); assistant p95; refusal rate; tool success rate; cache hit ratio; embedding model drift (per `model` column).
