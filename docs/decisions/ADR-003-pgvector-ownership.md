# ADR-003: pgvector ownership via raw SQL, not Prisma

- **Status**: accepted
- **Date**: 2026-08-10

## Context

Prisma does not support pgvector column types natively, and adding `unsupported("vector(1536)")` couples the API's migration pipeline to vector details the API never reads.

## Decision

- The `product_embeddings` table lives in PostgreSQL and is created by the initial API migration (appended raw SQL: extension, table, HNSW index).
- All reads/writes to that table happen only in `apps/ai-service` (`app/rag/store/pgvector_store.py`) via parameterized psycopg3 SQL.
- Prisma models the relational tables but not the vector column.

## Consequences

- One migration pipeline remains (API runs `migrate deploy`); the AI service never runs migrations.
- The AI service owns vector semantics (model column, HNSW, filter predicates) without Prisma friction.
- Risk: two tools writing DDL — mitigated by a strict ownership boundary and CI evaluation that asserts index presence.
