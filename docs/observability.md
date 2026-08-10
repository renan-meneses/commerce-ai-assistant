# Observability

## Stack

| Signal | Tool | Where |
|---|---|---|
| Traces | Langfuse (LLM-native) | `docker compose --profile full up -d` → :3002 |
| Traces (OTLP) | OpenTelemetry SDK → collector | collector :4317/:4318 |
| Metrics | Prometheus + OTel | :9090; collector mirrors OTLP metrics :8889 |
| Dashboards | Grafana | :3001 (provisioned dashboard `commerce-ai`) |
| Logs | pino (API, JSON), stdlib logging (AI service) | stdout |

## Traces

- **AI service**: `init_tracing` starts the OTLP exporter when `TRACING_ENABLED=true`. Langfuse is instrumented via callbacks in the `OpenAIAdapter` (`get_langfuse_handler`), gated by `LANGFUSE_ENABLED` + keys. The collector batches and forwards to Langfuse's OTLP endpoint with Basic auth from `OTEL_LANGFUSE_AUTH`.
- **API**: correlation-id interceptor assigns `x-request-id` per request; the AI service forwards it so `requestId` spans the web → API → AI service → graph → DB hop.

## Metrics

- NestJS `@nestjs/terminus` health (`/api/v1/health`); OTel FastAPI instrumentation exposes `/metrics`.
- AI service counters: `commerce_ai_chat_requests_total`, `commerce_ai_chat_duration_seconds` histogram (logged and exposed via Prometheus client in `app/api/routes/metrics`).
- The provisioned Grafana dashboard shows service `up`, API request rate, p95 latency, and AI chat traffic.

## Logging policy

- API: pino JSON with `requestId`, duration, status.
- AI service: structured log lines for security flags (`security: refusing request …`), provider fallbacks, indexing progress.
- **Sensitive data**: `mask_sensitive` redacts `sk-*` keys, JWTs, and bearer tokens before anything is logged or traced; the injection scanner exposes `sanitize_for_logging`.

## Health endpoints

- `GET /api/v1/health` — DB + Redis checks.
- `GET /health` (AI service) — vector store + cache checks, indexed chunk count, LLM configured flag.

## Runbook essentials

- Langfuse unavailable → traces silently drop (callbacks optional); the agent still answers.
- Redis down → `CacheService` degrades to no-op; tools call the API directly.
- RabbitMQ down → the API still serves reads/writes; indexing events queue up only while the broker is up (publisher reconnects).
- Prometheus/Grafana down → no impact on serving.
