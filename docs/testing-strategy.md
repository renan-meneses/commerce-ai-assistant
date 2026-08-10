# Testing Strategy

## Layers

| Layer | Tool | Command |
|---|---|---|
| API unit | Jest | `cd apps/api && yarn test` |
| API e2e | Jest + supertest (real PG/Redis/RabbitMQ) | `yarn test:e2e` |
| AI unit | pytest + respx | `cd apps/ai-service && .venv/bin/python -m pytest tests/ -q` |
| AI behavioral (graph) | pytest, stubbed retriever/tools | `pytest tests/test_agent_graph.py` |
| Retrieval eval | `app.evaluation.cli --suite rag` | `make evaluate-rag` |
| Agent eval | `app.evaluation.cli --suite agent` | `make evaluate-agent` |
| Lint / format / types | ESLint+Prettier / ruff / tsc / mypy | Makefile `lint-*` `typecheck-*` |

## API tests

- **Unit (15 tests)**: products, inventory, auth, orders services — mocked repositories, pure domain assertions (price math, inventory reservation, order lifecycle).
- **E2E (8 tests)**: boot the full Nest app against real PG/Redis/RabbitMQ — register/login, product pagination, cart add/update/remove, checkout→order creation, validation rejection. Requires `DATABASE_URL`, `REDIS_URL`, `RABBITMQ_URL` (see `test/jest-e2e.js`).

## AI service tests

Cover the deterministic core — no LLM or network required:

- **Chunker**: single-chunk short docs, word-boundary packing, deterministic ids, version-sensitivity.
- **Document builder**: dict/string categories, price bands, whitespace normalization.
- **Fusion + reranker**: RRF ordering/provenance, weighted fusion, deterministic rerank.
- **Security**: injection patterns, refusal policy, auth-required tools, doc-content scanning, masking.
- **Router**: tier mapping, model selection, provider fallback, fallback-disabled errors.
- **Tools**: registry contents, auth flags, 429 retry via respx, 4xx surfacing.
- **pgvector helpers**: URL translation, stopword/OR tsquery building.
- **Agent graph** (`test_agent_graph.py`): full graph with `ScriptedLLMProvider` + stubs — inventory flow, injection refusal before tools, unauthenticated private-tool denial, deterministic tool selection, empty-loop behavior.

## Evaluations

- `rag_questions.json` (10 pt-BR questions) against the seeded catalog; metrics: recall@k, top-1 category precision, token-overlap feature recall. Pass bar: ≥0.8 / ≥0.8 / ≥0.6.
- `behavioral_cases.json` (10 cases): tool-triggered intents (inventory, price, order status, shipping), RAG usage, injection/admin/prompt-extraction refusal, auth enforcement. Pass bar: 100%.
- Reports land in `evaluation/reports/evaluation-report-<ts>.md`.
- RAG eval requires indexed vectors — CI indexes with hash embeddings (`EMBEDDINGS_USE_HASH=true`).

## CI gates

`ci.yml`: API (lint → typecheck → build → migrate → seed → unit → e2e) and AI service (ruff → format → mypy → pytest). `ai-evaluation.yml` runs both suites against a fresh pgvector database and uploads the report artifact.

## Coverage targets

Unit/behavioral suites are the gate; line-coverage thresholds are intentionally not enforced in CI yet — the evaluation suites (which assert product behavior, not coverage) are the primary quality signal.
