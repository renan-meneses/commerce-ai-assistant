# Resume Guide — Commerce AI Assistant

> Última atualização: 2026-08-10 (Phase 3 — stack completa de pé, gaps 1 e 3 fechados)

## Estado atual

- Branch `main`, sincronizado com `origin/main`.
- Todos os itens de `docs/tasks.md` (T-001 … T-112) estão `DONE`.
- 8 commits fecham o trabalho (versus os 24 planejados em `commit-plan.md`,
  que foi mesclado em commits maiores):

| Commit | Conteúdo |
|--------|----------|
| `1b30f65` | Monorepo + infraestrutura Docker local (postgres+pgvector, redis, rabbitmq), Makefile, .env.example, docs base |
| `2b5352f` | Fundação NestJS API (health, config, Swagger, Prisma) |
| `e9fe9ef` | AI service: langgraph agent, pipeline RAG híbrido, ferramentas de comércio, worker de indexação, avaliações |
| `de3050c` | Containerização (Dockerfiles api/ai-service/worker), web app React, CI/CD (ci/security/ai-evaluation), observabilidade (otel, prometheus, grafana, langfuse) |
| `a83fd25` | Documentação completa: README, architecture, rag, agent, database, security, observability, testing, ci-cd, architecture-review, interview-guide, ADR-001…008, licença |
| `4a5b53f` | docs/resume.md + `.env.example` (EMBEDDINGS_USE_HASH, OTEL_LANGFUSE_AUTH) |
| `1d2c83e` | Fixes de runtime container: tsconfig.build (dist/main.js), prisma openssl-3 no alpine, `@Type` no chat DTO (messages [[ ]]), healthcheck /api/v1/health, langfuse:2, EMBEDDINGS_USE_HASH default |
| `b06ff0a` | Rate limiting Redis no AI service + token de serviço escopado (x-service-token, aud=ai-service, 5min) |

## Verificações já realizadas (Phase 3)

- Stack completa de pé: `docker compose --profile full up -d` (11 serviços) — api, ai-service,
  worker, web, langfuse, prometheus, grafana, otel, postgres, redis, rabbitmq.
- Healths: api `/api/v1/health` 200, ai-service `/health` 200, langfuse/prometheus/grafana 200.
- Seed: 59 produtos; reindex `python -m app.indexing.cli --reindex-all` → 59 chunks (hash embeddings).
- Proxy de chat validado ponta a ponta (auth → DTO → forwarding → agente); sem chave LLM o
  agente falha com 500 controlado (esperado).
- Fix importante: DTO de chat convertia `messages` em `[[]]` (enableImplicitConversion) — corrigido com `@Type`.
- Testes: ai-service 44 passam, api 18 passam; lint 0 erros; builds Docker ok.

## Pendências conhecidas (gaps honestos)

Documentados em `docs/architecture-review.md`:

1. ~~Fluxo de token de serviço API → AI service~~ **FECHADO** (`b06ff0a`).
2. ~~Rate limiting no AI service~~ **FECHADO** (`b06ff0a`).
3. **Quality gate de modelo LLM** (benchmark/regressão de respostas) pendente.
4. **Validação de chat com chave LLM real** pendente (aguarda OPENAI_API_KEY no `.env`).
5. `apps/api/.env.example` e `apps/ai-service/.env.example` não existem — há apenas o `.env.example` raiz.
6. DLQ re-drive script documentado mas não commitado.
7. Web app sem testes.

## Próximos passos sugeridos (Phase 4)

1. Adicionar `OPENAI_API_KEY` ao `.env` e validar chat real com tracing no Langfuse
   (grafana :3001, langfuse :3002).
2. Implementar quality gate de modelo (golden-answer eval com chave, semanal).
3. Commitar script de re-drive do DLQ (`scripts/requeue_dlq.py`).
4. Adicionar testes ao web app (vitest + MSW, refresh de token).
5. Atualizar `docs/resume.md` ao final de cada sessão.

## Como retomar

- Ambiente: `docker compose --profile full up -d` (ou `make up`/`make dev` conforme Makefile).
- Testes: `make test` (ou `make test-api` / `make test-ai`).
- Lint: `make lint` (`ruff` no ai-service, eslint/tsc no api e web).
- Docs vivos: `docs/tasks.md`, `docs/commit-plan.md`, `docs/resume.md`, `docs/architecture-review.md`.
