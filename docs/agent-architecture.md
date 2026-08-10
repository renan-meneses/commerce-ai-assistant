# Agent Architecture

## Graph

Built with LangGraph 1.x (`app/graph/workflow.py`). Nodes are wired with `functools.partial` to inject dependencies (deps) while keeping node signatures LangGraph-compatible.

```
analyze (security scan)
  └─ classify (intent via cheap model; REFUSED if flagged)
       └─ extract (structured requirements, cheap model)
            └─ route
                 ├─ RAG intents → retrieve → rerank ─┐
                 ├─ tool intents → select_tool → execute_tool (loop) ─┘
                 │                                     └─ route_tool_loop (max iterations)
                 └─ REFUSED ───────────────────────────┐
                                                      ▼
                                              generate_response → validate → END
```

## State

`AgentState` is a TypedDict (all keys optional) — messages are appended via LangGraph's `add_messages` reducer; tool results, sources, iterations, pending tools and security flags are plain keys. `_max_iterations` guards the tool loop (default 5, from settings).

## Intent → tool mapping is deterministic

The LLM never chooses its own tools. `select_tool` maps:

| Intent | Tool |
|---|---|
| ORDER_STATUS (with order number) | `get_order_status` |
| ORDER_STATUS (no number) | `get_user_orders` |
| PRODUCT_PRICE | `get_product_price` |
| INVENTORY | `get_inventory` |
| SHIPPING | `calculate_shipping` |
| PRODUCT_SEARCH / RECOMMENDATION / COMPARE / KNOWLEDGE | RAG path |

## Security model

Layered (see `docs/security.md` for depth):

1. **Injection scanner** on inbound text (pattern groups: instruction override, prompt reveal, role override, admin actions, discount override, SQL, tool abuse) — flagged requests are classified REFUSED without any LLM call.
2. **Permission enforcement in `execute_tool`** — `get_order_status`/`get_user_orders` require an authenticated `user_id`; enforcement happens regardless of what the model says.
3. **No write tools** in the registry.
4. **Retrieved-content scanning** — flags injection attempts embedded in product docs before they reach the prompt.
5. **Pydantic re-validation** of every structured LLM output; the response node re-checks for leaked system prompts.

## Tool framework

`app/tools/base.py` defines `ToolResult`, the `Tool` protocol and `ToolAuthContext`. Tools are bounded HTTP calls to the commerce API (`app/tools/commerce_client.py`) with retry/backoff on 429/5xx. The registry (`app/tools/registry.py`) is the single list of capabilities exposed to the agent.

## Model routing

`ModelRouter` maps tasks to tiers: intent/extract → cheap model (`gpt-4o-mini`), recommendation/compare → strong model (`gpt-4o`). Providers are tried in order with fallback; `LLM_MODEL_FALLBACK_ENABLED=false` disables degradation. Structured output uses native JSON-schema mode + local Pydantic validation.

## Failure behavior

- Provider exhaustion → `LLMError` → 500 with a generic message; no partial tool side effects (tools are read-only).
- Iteration cap exceeded → the tool loop terminates and the last known state is answered.
- Unknown tool in state (should never happen with the fixed mapping) → `ToolResult(ok=False)`.
