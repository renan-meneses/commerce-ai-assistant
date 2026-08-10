# Task Management — commerce-ai-assistant

> Status values: `TODO` · `IN_PROGRESS` · `DONE` · `BLOCKED`

## Phase 1 — Foundation

| ID | Description | Status | Dependencies | Acceptance Criteria | Tests Required | Docs |
|----|-------------|--------|--------------|---------------------|----------------|------|
| T-001 | Initialize monorepo structure (apps/, packages/, infrastructure/, docs/, evaluation/, scripts/) | DONE | — | Folders exist; git initialized on `main` | — | commit-plan.md |
| T-002 | Add local Docker infrastructure (postgres+pgvector, redis, rabbitmq) with healthchecks | DONE | T-001 | `docker compose up -d postgres redis rabbitmq` starts healthy services | — | README, architecture.md |
| T-003 | Add root tooling (.env.example, Makefile, .gitignore) | DONE | T-001 | Make targets resolve; env template covers all services | — | README |
| T-004 | NestJS API skeleton with health endpoint and Swagger | DONE | T-002 | `GET /health` returns 200; Swagger at `/docs` | unit test for health | architecture.md |
| T-005 | FastAPI AI service skeleton with health endpoint | DONE | T-002 | `GET /health` returns 200 | unit test for health | architecture.md |
| T-006 | React web skeleton (Vite) | DONE | — | App renders; dev server runs | — | README |

## Phase 2 — Commerce Domain

| ID | Description | Status | Dependencies | Acceptance Criteria | Tests Required | Docs |
|----|-------------|--------|--------------|---------------------|----------------|------|
| T-010 | Prisma schema: users, categories, products, inventory, carts, cart_items, orders, order_items | DONE | T-004 | Migrations apply cleanly | — | database-design.md |
| T-011 | Product domain module (controller/service/repository pattern, DTOs, validation) | DONE | T-010 | CRUD + pagination + filters; Swagger documented | unit + e2e | database-design.md |
| T-012 | Inventory module (quantity, reserved quantity, availability) | DONE | T-010 | Availability checks; no negative stock | unit + e2e | database-design.md |
| T-013 | Cart module (add/update/remove items) | DONE | T-010 | Cart totals computed server-side | unit + e2e | database-design.md |
| T-014 | Orders module (create order from cart, order status, order items) | DONE | T-012, T-013 | Order creation transactional; stock decremented | unit + e2e | database-design.md |
| T-015 | Users + Auth (register, login, JWT, guards) | DONE | T-010 | Protected routes reject anonymous requests | unit + e2e | security.md |
| T-016 | Seed data (20 notebooks, 20 smartphones, 10 monitors, 10 accessories) | DONE | T-010 | `prisma db seed` populates realistic data | — | database-design.md |

## Phase 3 — AI Foundation

| ID | Description | Status | Dependencies | Acceptance Criteria | Tests Required | Docs |
|----|-------------|--------|--------------|---------------------|----------------|------|
| T-020 | LLM provider abstraction (`LLMProvider` Protocol, OpenAI adapter) | DONE | T-005 | Provider injectable; structured output supported | unit (mocked) | decisions/ADR-007 |
| T-021 | Embedding abstraction + OpenAI adapter + local fallback | DONE | T-005 | Embeddings return normalized vectors | unit (mocked) | rag-architecture.md |
| T-022 | Structured output schemas (intent, requirements, ranking, recommendation) | DONE | T-020 | Pydantic models validated before use | unit | agent-architecture.md |
| T-023 | FastAPI contracts: `POST /ai/chat`, auth propagation, correlation IDs | DONE | T-020 | Contract validated against API service | integration | architecture.md |

## Phase 4 — RAG

| ID | Description | Status | Dependencies | Acceptance Criteria | Tests Required | Docs |
|----|-------------|--------|--------------|---------------------|----------------|------|
| T-030 | Document builder (product → normalized text + metadata) | DONE | T-016 | Deterministic document text; metadata enriched | unit | rag-architecture.md |
| T-031 | Chunking (product specs-aware, deterministic IDs) | DONE | T-030 | Chunks idempotent; no duplicates on re-run | unit | rag-architecture.md |
| T-032 | pgvector storage (product_embeddings, vector index, param SQL layer) | DONE | T-010, T-031 | HNSW/IVFFlat index present; raw SQL layer | integration | decisions/ADR-003, rag-architecture.md |
| T-033 | Semantic search (embedding → vector similarity) | DONE | T-032 | Correct top-k; metadata filters work | integration | rag-architecture.md |
| T-034 | Keyword search (PostgreSQL FTS + trigram) | DONE | T-032 | Lexical matches found | integration | rag-architecture.md |
| T-035 | Hybrid search + fusion (RRF + score fusion) | DONE | T-033, T-034 | Fused results ranked deterministically | unit + integration | rag-architecture.md |
| T-036 | Reranker abstraction + SimpleScoreReranker | DONE | T-035 | Reranker pluggable | unit | rag-architecture.md |

## Phase 5 — Agent

| ID | Description | Status | Dependencies | Acceptance Criteria | Tests Required | Docs |
|----|-------------|--------|--------------|---------------------|----------------|------|
| T-040 | LangGraph AgentState + graph skeleton | DONE | T-020 | State typed; graph compiles | unit | decisions/ADR-004 |
| T-041 | Intent classification + routing node | DONE | T-022 | Intent → correct branch (RAG vs tools) | behavioral | agent-architecture.md |
| T-042 | Requirements extraction node | DONE | T-022 | Price/category/features extracted | behavioral | agent-architecture.md |
| T-043 | RAG node + response generation + validation | DONE | T-036, T-041 | Answer grounded in retrieved docs | behavioral | agent-architecture.md |
| T-044 | Graph limits (iteration cap, cycle guard) | DONE | T-040 | Workflow terminates within budget | unit | agent-architecture.md |

## Phase 6 — Tools

| ID | Description | Status | Dependencies | Acceptance Criteria | Tests Required | Docs |
|----|-------------|--------|--------------|---------------------|----------------|------|
| T-050 | Tool framework (schema, validation, error handling, auth) | DONE | T-022 | Tools never execute raw SQL | unit | security.md |
| T-051 | `search_products`, `get_product_details`, `compare_products` | DONE | T-050 | Call API service via HTTP | unit + behavioral | agent-architecture.md |
| T-052 | `get_product_price`, `get_inventory` | DONE | T-050 | Short-TTL/no-cache values; live data | unit + behavioral | agent-architecture.md |
| T-053 | `get_user_orders`, `get_order_status` (auth required) | DONE | T-050 | Unauthorized users rejected | unit + behavioral | security.md |
| T-054 | `calculate_shipping` | DONE | T-050 | Deterministic estimate | unit | agent-architecture.md |

## Phase 7 — Async Indexing

| ID | Description | Status | Dependencies | Acceptance Criteria | Tests Required | Docs |
|----|-------------|--------|--------------|---------------------|----------------|------|
| T-060 | RabbitMQ setup (exchange, queue, dead-letter) | DONE | T-002 | Queue declared with DLQ | integration | decisions/ADR-006 |
| T-061 | API emits product events (created/updated) | DONE | T-011 | Event published on write | integration | architecture.md |
| T-062 | Indexing worker (consume → build → embed → upsert) | DONE | T-060, T-031, T-032 | Event processed; pgvector updated | integration | rag-architecture.md |
| T-063 | Retry policy + DLQ + idempotency (deterministic doc IDs, versioning) | DONE | T-062 | Replayed events do not duplicate | integration | rag-architecture.md |

## Phase 8 — Observability

| ID | Description | Status | Dependencies | Acceptance Criteria | Tests Required | Docs |
|----|-------------|--------|--------------|---------------------|----------------|------|
| T-070 | Correlation IDs across API → AI service → graph → DB → LLM | DONE | T-023 | Same trace id through all hops | integration | observability.md |
| T-071 | Prometheus metrics (HTTP latency, request/error counts, queue processing, cache hit rate) | DONE | T-004 | Metrics endpoint exposed | unit | observability.md |
| T-072 | Grafana dashboard config | DONE | T-071 | Dashboards provisioned | — | observability.md |
| T-073 | Langfuse tracing (intent, retrieval, docs, tools, prompt, tokens, latency) | DONE | T-020 | Trace with masking support | unit (mocked) | decisions/ADR-008, observability.md |

## Phase 9 — Security

| ID | Description | Status | Dependencies | Acceptance Criteria | Tests Required | Docs |
|----|-------------|--------|--------------|---------------------|----------------|------|
| T-080 | Prompt injection defenses (delimiter policy, tool permission model, output validation) | DONE | T-050 | Injection attempts refused | behavioral | security.md |
| T-081 | Rate limiting (API + AI endpoints) | DONE | T-004 | Limits enforced; headers present | unit | security.md |
| T-082 | Input validation & schema checks everywhere | DONE | T-011, T-050 | Invalid payloads rejected | unit | security.md |
| T-083 | Semgrep config + security scan in CI | DONE | — | Scan runs in CI | — | ci-cd.md |

## Phase 10 — Evaluation

| ID | Description | Status | Dependencies | Acceptance Criteria | Tests Required | Docs |
|----|-------------|--------|--------------|---------------------|----------------|------|
| T-090 | Evaluation datasets (RAG questions + behavioral cases) | DONE | T-016 | JSON datasets with expected fields | — | testing-strategy.md |
| T-091 | Retrieval evaluation (precision/recall at k) | DONE | T-035 | Report generated | unit | testing-strategy.md |
| T-092 | Behavioral tests (tool selection, RAG usage, injection refusal) | DONE | T-041 | 5+ scenarios pass | behavioral | testing-strategy.md |
| T-093 | `make evaluate-ai` CLI generating report | DONE | T-091 | Report written to evaluation/reports | — | testing-strategy.md |

## Phase 11 — Documentation

| ID | Description | Status | Dependencies | Acceptance Criteria | Tests Required | Docs |
|----|-------------|--------|--------------|---------------------|----------------|------|
| T-100 | README complete with Mermaid diagrams | DONE | all | All sections present | — | README |
| T-101 | Architecture docs (architecture, system-design, rag, agent, database, security, observability, testing, ci-cd) | DONE | all | Each doc written | — | docs/ |
| T-102 | ADRs (001–008) | DONE | all | Context/Decision/Alternatives/Consequences/Trade-offs | — | docs/decisions/ |
| T-103 | Interview guide | DONE | T-100 | Sections per spec | — | docs/interview-guide.md |
| T-104 | Architecture review (debt, risks, bottlenecks) | DONE | all | Findings classified | — | docs/architecture-review.md |

## CI/CD

| ID | Description | Status | Dependencies | Acceptance Criteria | Tests Required | Docs |
|----|-------------|--------|--------------|---------------------|----------------|------|
| T-110 | GitHub Actions: ci.yml (install, lint, unit, integration, behavioral, docker build) | DONE | all | Pipeline green | — | ci-cd.md |
| T-111 | GitHub Actions: security.yml (semgrep, audit) | DONE | T-083 | Pipeline green | — | ci-cd.md |
| T-112 | GitHub Actions: ai-evaluation.yml (optional, manual trigger) | DONE | T-093 | Runs on demand | — | ci-cd.md |
