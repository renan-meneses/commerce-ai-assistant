# CI/CD

## Workflows

| Workflow | Triggers | Purpose |
|---|---|---|
| `.github/workflows/ci.yml` | push to main, PRs | API and AI service quality gates |
| `.github/workflows/ai-evaluation.yml` | push to main, manual | Runs retrieval + behavioral suites against a fresh pgvector DB; uploads report artifact |
| `.github/workflows/security.yml` | push/PR to main, weekly (Mon 06:00 UTC) | Semgrep scan with `.semgrep.yml` rules |

## CI pipeline (api job)

1. Checkout, setup-node (yarn cache)
2. `yarn install --frozen-lockfile`
3. `prisma generate` → `lint` → `typecheck` → `build`
4. `prisma migrate deploy` (fresh pgvector service container)
5. `prisma db seed` (catalog for e2e)
6. Unit tests → e2e tests (real PG/Redis/RabbitMQ service containers)

## CI pipeline (ai-service job)

1. setup-python 3.13 with pip cache
2. `pip install -e ".[dev]"`
3. `ruff check` → `ruff format --check` → `mypy app`
4. `pytest tests/ -q`

## Evaluation workflow

Boots a full stack in service containers: pgvector Postgres, Redis, RabbitMQ. Then:

1. API migrate + seed, boot API (`yarn start:prod`), wait on `/api/v1/health`
2. Index the catalog with hash embeddings (`EMBEDDINGS_USE_HASH=true python -m app.indexing.cli --reindex-all`)
3. Run `--suite rag` and `--suite agent`
4. Upload `evaluation/reports/` as an artifact

No API keys required — deterministic embeddings and scripted LLM responses.

## Security scan

Semgrep rules (`apps/*`, `.semgrep.yml`): hardcoded secrets/keys, `eval`/`exec`, shell-from-HTTP, string-concatenated SQL, dangerous casts. Scans on every PR and weekly on main.

## Container images

- `apps/api/Dockerfile` — multi-stage: install+`prisma generate`+`nest build` → runtime with production deps only, non-root `node` user.
- `apps/ai-service/Dockerfile` — python 3.13-slim, installs package, runs `uvicorn` on :8000.
- `apps/ai-service/Dockerfile.worker` — same base, entrypoint `python -m app.indexing.worker_main`.

Built/verified locally via `docker compose build api ai-service worker`.

## Deployment notes (out of scope for this repo, for the reviewer)

- Migration step must run before rollout (`prisma migrate deploy` in the release job).
- The HNSW index build is lazy in pgvector — schedule an `ANALYZE` + optional `REINDEX` on the embeddings table after large backfills.
- RabbitMQ DLQ (`commerce.product.dlx`) should be surfaced with alerting + a re-drive script.
- Embedding model changes require a full `--reindex-all` with a new `model` value (queries filter on `model`).
