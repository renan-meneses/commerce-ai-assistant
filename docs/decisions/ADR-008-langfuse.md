# ADR-008: Langfuse for LLM observability

- **Status**: accepted
- **Date**: 2026-08-10

## Context

LLM apps fail differently from CRUD apps: the question is usually "what prompt, what docs, what tool call produced this bad answer". We need trace-level visibility into the agent loop plus standard metrics.

## Decision

- **Langfuse** for LLM traces: callbacks attached in `OpenAIAdapter` (gated by `LANGFUSE_ENABLED`), capturing prompt templates, retrieved documents, tool calls, tokens, latency and the decision flow.
- **OpenTelemetry** (OTLP → collector) for infrastructure-level traces/metrics; the collector mirrors metrics to Prometheus and forwards traces to Langfuse's OTLP endpoint.
- **Prometheus/Grafana** for service SLO dashboards (request rate, p95, chat traffic).

## Consequences

- One UI (:3002) to debug prompt/doc/tool interactions with full run provenance.
- Traces are redacted (`mask_sensitive`) before shipping; instrumentation is optional at runtime — failure degrades to no-op.
- Cost: a Langfuse instance to run (or SaaS); OTLP auth must be configured (`OTEL_LANGFUSE_AUTH`).
