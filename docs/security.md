# Security

## Threat model

The assistant is a public surface. Primary threats:

1. **Prompt injection** — user text (or retrieved documents) overriding agent behavior.
2. **Data exfiltration** — forcing the model to reveal system prompts or another user's orders.
3. **Privilege escalation** — triggering admin/price/stock mutations through natural language.
4. **Abuse** — scraping, rate-limit bypass, enumeration.
5. **Supply chain** — dependencies, secrets in code/traces.

## Defenses

### Input (AI service)

- **InjectionScanner** (`app/security/injection.py`) — 8 pattern groups (ignore-instructions, reveal-prompt, role-override, admin-action, discount-override, SQL injection, tool-abuse). Flagged input short-circuits to `REFUSED` before any LLM call.
- **Retrieved-document scanning** — product content is scanned before entering the prompt; hits are flagged per document.
- **Prompt-level policy** — the system prompt declares retrieved content untrusted (defense in depth, not a guarantee).

### Permissions

- **Tool registry is read-only** — `WRITE_TOOLS == set()`; no mutation tool exists to hijack.
- **Auth-required tools** — `get_order_status`/`get_user_orders` require a scoped service token
  (minted by the API, `aud=ai-service`, 5 min, forwarded as `x-service-token`); enforced in
  `execute_tool` regardless of model output. The commerce API re-enforces ownership with the
  token's `sub`.
- **Intent→tool mapping is deterministic** — the LLM cannot select capabilities; it only fills bounded tool arguments.

### Output

- Every structured LLM response is **re-validated with Pydantic** before use (`response_model`).
- The response node re-checks for leaked prompts.

### Transport & API

- JWT bearer auth (`@nestjs/jwt`, expiry 2h); cart/orders endpoints scoped to the authenticated user.
- Helmet CSP + `@nestjs/throttler` rate limiting (60 req/min default; headers exposed); the commerce client retries 429/5xx with backoff.
- ValidationPipe with `whitelist + forbidNonWhitelisted` on every DTO.

### Data & observability

- Passwords hashed (argon2), JWT secret from env only.
- `mask_sensitive` redacts API keys, JWTs and bearer tokens in logs/traces; Langfuse instrumentation is gated by `LANGFUSE_ENABLED`.
- No secrets committed: `.env.example` ships placeholders; CI injects ephemeral values.

### Supply chain

- Lockfiles committed (yarn.lock / pip constraints via pyproject).
- Weekly semgrep scan (`.semgrep.yml`) blocks hardcoded secrets, `eval/exec`, shell-from-HTTP, string-concatenated SQL.

## Responsible reporting

Report issues privately to the repository maintainers; do not open public advisories before coordinated disclosure.

## Residual risks (acknowledged)

- Heuristic injection scanning is not provably complete — mitigated by read-only tools and auth enforcement.
- Hash embeddings in dev/CI are not meaningful for production semantic quality (documented; `EMBEDDINGS_USE_HASH` must be false in prod).
- The AI service forwards a short-lived scoped service token for order tools; the token only identifies the caller (`sub`), and the commerce API enforces ownership. Token minting/forwarding covered by unit tests.
