# Interview Guide

A 45-minute walkthrough of this repository, designed to show senior-level thinking: why things are built this way, what broke, and what would change in production.

## 1. The pitch (2 min)

"An AI-powered e-commerce platform: a NestJS commerce API, a FastAPI + LangGraph assistant with hybrid RAG over pgvector, and a React storefront. The interesting part is the trust boundary — the LLM can never touch the database."

## 2. Architecture story (10 min)

Start at `docs/architecture.md`. Walk: web → API (auth, catalog, orders) → RabbitMQ events → worker (indexing) → pgvector; and web → API `/ai/chat` → FastAPI graph. Point to the two key decisions:

- **ADR-002** (service split): the assistant must not share a transaction path with the commerce domain.
- **ADR-003** (pgvector ownership): Prisma can't model vectors; the AI service owns the vector column via raw parameterized SQL; deterministic chunk ids make upserts idempotent.

## 3. The agent (10 min) — `docs/agent-architecture.md`

Explain the LangGraph flow with the actual file open (`app/graph/workflow.py`):

- `analyze` runs the injection scan; flagged input becomes REFUSED **without an LLM call**.
- Intent→tool mapping is deterministic — the model fills tool arguments, never capabilities.
- `execute_tool` re-checks auth regardless of the model output.
- Iteration caps bound the tool loop.

Be ready for: "Why not native tool calling?" Answer: the intent space is small, deterministic mapping is cheaper and auditable, and the security model doesn't depend on the model behaving.

## 4. RAG (8 min) — `docs/rag-architecture.md`

- Hybrid retrieval: cosine (HNSW) + FTS `ts_rank` with **OR-term semantics** and a small stopword list; RRF fusion; deterministic reranking.
- The war story: `plainto_tsquery` AND semantics made "compare ASUS Vivobook and Lenovo IdeaPad" unanswerable — the evaluation caught it, keyword search switched to OR + stopwords, and recall went 0.95 → 1.00. This is the "evaluations found a real bug" story.
- Idempotency: sha256 chunk ids, delete-before-upsert, replay-safe consumers.

## 5. Evaluations (8 min)

Run `make evaluate-ai` (or show a report from `evaluation/reports/`):

- 10 behavioral cases (tool routing, injection refusal, auth enforcement) — 100% required.
- 10 RAG questions aligned with the seeded pt-BR catalog — recall@k / category precision / feature recall.
- No keys needed: `ScriptedLLMProvider` + deterministic hash embeddings for CI; the report is a CI artifact.

Emphasize: the dataset was rewritten to match the real catalog, and the feature metric is token-overlap — the eval measures the system that actually ships, not a toy.

## 6. Security (5 min) — `docs/security.md`

Layers: input scanning → no-write tool registry → auth enforcement at execution → Pydantic re-validation of outputs → masking in logs/traces → rate limiting → semgrep in CI. Then the honest gaps from `docs/architecture-review.md` (service token flow, AI-service rate limiting).

## 7. Testing & CI (5 min) — `docs/testing-strategy.md`, `docs/ci-cd.md`

39 pytest tests (chunker, fusion, scanner, router, graph with stubs), 15 unit + 8 e2e in the API, ruff/mypy/ESLint gates, an evaluation workflow that boots the whole stack in containers and uploads reports.

## 8. Questions to ask back (prepared)

- "The AI service passes user_id where a token is expected — how would you design a scoped service token flow?"
- "How would you move retrieval to a vector database without touching the API?"
- "What metric would you alert on first for the assistant?"

## Known facts to cite

- 59 seeded products, demo user `demo@commerce.ai` / `demo1234`.
- Initial migration `20260810175929_init` embeds pgvector + HNSW.
- 4 commits: `1b30f65` infra, `2b5352f` API, `e9fe9ef` AI service, `de3050c` infra/web/CI.
- Both eval suites pass 20/20; RAG metrics 1.000/1.000/1.000.
