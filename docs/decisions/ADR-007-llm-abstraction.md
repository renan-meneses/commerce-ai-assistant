# ADR-007: LLM provider abstraction behind a typed Protocol

- **Status**: accepted
- **Date**: 2026-08-10

## Context

Vendor lock-in is a real risk: OpenAI, OpenRouter, Anthropic and Gemini all expose different SDKs, and model quality changes quarterly. The agent domain must not import vendor SDKs.

## Decision

`app/llms/base.py` defines:

- `Message`, `LLMResponse`, `LLMError`, `LLMValidationError`
- `LLMProvider` (Protocol) with `generate(messages, *, model, response_model, temperature, max_tokens, callbacks)`

Adapters (`OpenAIAdapter`, scripted test provider) implement the protocol. `ModelRouter` picks tiers per task and falls back across providers. Embeddings get the same treatment (`EmbeddingProvider`: `embed_documents`/`embed_query`).

## Consequences

- Vendor swap = new adapter, zero graph changes.
- Tests run against a scripted provider — no keys needed in CI.
- Structured output contracts (`response_model`) are enforced at the boundary: the LLM output is untrusted until Pydantic re-validates it.
- Cost: a thin adapter layer to maintain; the OpenAI adapter keeps optional Langfuse callbacks plumbing.
