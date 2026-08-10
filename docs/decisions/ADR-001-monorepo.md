# ADR-001: Monorepo structure

- **Status**: accepted
- **Date**: 2026-08-10

## Context

Three runtimes (NestJS API, FastAPI AI service, React web) share deployment, evaluation data, and development conventions. We need a structure that keeps them independently versionable while sharing tooling.

## Decision

A single repository with:

```
apps/api          NestJS commerce backend
apps/ai-service   FastAPI + LangGraph assistant + indexing worker
apps/web          React storefront
packages/         shared contracts (reserved)
evaluation/       datasets + reports
infrastructure/   docker compose, monitoring, postgres init
docs/             architecture docs + ADRs
```

## Consequences

- One PR can coordinate cross-service changes (schema + vector indexing + eval dataset).
- Language boundaries stay explicit; no shared build graph across apps.
- Yarn (apps/api, apps/web) and pip/venv (apps/ai-service) are per-app — no root workspace lockstep.
