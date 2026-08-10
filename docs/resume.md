# Resume Guide — Commerce AI Assistant

> Última atualização: 2026-08-10 (Phase 2 — documentação e infraestrutura concluída)

## Estado atual

- Branch `main`, sincronizado com `origin/main`.
- Todos os itens de `docs/tasks.md` (T-001 … T-112) estão `DONE`.
- 5 commits fecham o trabalho (versus os 24 planejados em `commit-plan.md`,
  que foi mesclado em commits maiores):

| Commit | Conteúdo |
|--------|----------|
| `1b30f65` | Monorepo + infraestrutura Docker local (postgres+pgvector, redis, rabbitmq), Makefile, .env.example, docs base |
| `2b5352f` | Fundação NestJS API (health, config, Swagger, Prisma) |
| `e9fe9ef` | AI service: langgraph agent, pipeline RAG híbrido, ferramentas de comércio, worker de indexação, avaliações |
| `de3050c` | Containerização (Dockerfiles api/ai-service/worker), web app React, CI/CD (ci/security/ai-evaluation), observabilidade (otel, prometheus, grafana, langfuse) |
| `a83fd25` | Documentação completa: README, architecture, rag, agent, database, security, observability, testing, ci-cd, architecture-review, interview-guide, ADR-001…008, licença |

## Verificações já realizadas

- `docker compose config` válido (todos os 11 serviços: postgres, redis, rabbitmq, api, ai-service, worker, web, otel-collector, prometheus, grafana, langfuse).
- Imagens `api`, `ai-service`, `worker` compilam via `docker compose build`.
- Smoke test: imagem `ai-service` sobe, `/health` OK, 59 chunks indexados no bootstrap.
- Chat falha com mensagem controlada quando não há chave LLM (comportamento esperado).
- Web app React: `yarn build` OK, preview serve, proxy para API funciona.
- Workflow de CI validado estruturalmente (comandos conferidos com os Makefiles).

## Pendências conhecidas (gaps honestos)

Documentados em `docs/architecture-review.md`:

1. **Fluxo de token de serviço API → AI service** não implementado de ponta a ponta
   (auth de serviço entre serviços).
2. **Rate limiting no AI service** ausente (existe no API).
3. **Quality gate de modelo LLM** (benchmark/regressão de respostas) pendente.
4. `.env.example` foi corrigido neste passo: adicionados `EMBEDDINGS_USE_HASH` e `OTEL_LANGFUSE_AUTH`.
5. `apps/api/.env.example` e `apps/ai-service/.env.example` não existem — há apenas o `.env.example` raiz.

## Próximos passos sugeridos (Phase 3)

1. Commit do ajuste em `.env.example` (verificação pendente nesta sessão).
2. Subir stack completa com observabilidade: `docker compose --profile full up -d` e validar
   grafana (:3001), langfuse (:3000), prometheus (:9090).
3. Executar validação end-to-end: seed, indexação de produtos, chat no web app com chave LLM
   (OpenRouter/OpenAI) e conferir tracing no Langfuse.
4. Fechar gaps do `architecture-review.md` (token service-to-service, rate limit no AI service).
5. Atualizar `docs/resume.md` ao final de cada sessão.

## Como retomar

- Ambiente: `docker compose --profile full up -d` (ou `make up`/`make dev` conforme Makefile).
- Testes: `make test` (ou `make test-api` / `make test-ai`).
- Lint: `make lint` (`ruff` no ai-service, eslint/tsc no api e web).
- Docs vivos: `docs/tasks.md`, `docs/commit-plan.md`, `docs/resume.md`.
