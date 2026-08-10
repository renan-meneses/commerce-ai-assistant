# ADR-004: LangGraph for the assistant control flow

- **Status**: accepted
- **Date**: 2026-08-10

## Context

The assistant needs a stateful multi-step flow (intent → requirements → retrieve/act → answer) with loops (tool execution, bounded iterations), conditional routing and human-in-the-loop readiness.

## Decision

Use **LangGraph** to model the agent as an explicit `StateGraph` (`app/graph/workflow.py`):

- typed state (`AgentState` TypedDict; `add_messages` reducer for conversation history),
- deterministic nodes and conditional edges,
- dependencies injected via `functools.partial(deps=...)` to keep node signatures LangGraph-compatible (async nodes return dicts; no lambda-wrapped coroutines).

## Consequences

- Graph structure is reviewable and testable (behavioral suite runs the real graph with scripted providers).
- Iteration caps and tool-loop exit conditions are explicit state transitions.
- Cost: LangGraph 1.x semantics (message objects, state key declaration) must be respected — missing TypedDict keys are silently dropped, which caused real bugs during development (documented in the evaluation work).
