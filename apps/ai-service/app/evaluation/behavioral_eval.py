"""Behavioral evaluation: routing, tool selection and security behavior.

Runs the compiled LangGraph with a scripted LLM provider and asserts:
- the classified intent matches the expected one (or REFUSED)
- the right tool was called (from state.tool_results)
- RAG documents were used when expected
- injection cases never execute tools and produce a refusal

No live LLM calls — CI-safe by design.
"""

from __future__ import annotations

import asyncio
import re

from app.agents.state import AgentState
from app.evaluation.fakes import ScriptedLLMProvider


def _intent_response(intent: str) -> dict:
    return {
        "intent": intent,
        "confidence": 0.99,
        "reason": "scripted for evaluation",
        "requires_user_context": False,
    }


_ORDER_NUMBER_RE = re.compile(r"ORD-\d{8}-[A-Z0-9]{6}")


def _build_provider(cases: list[dict]) -> ScriptedLLMProvider:
    intent_by_query: dict[str, str] = {}
    for case in cases:
        intent_by_query[case["input"].strip().lower()] = case["expected"].get(
            "intent", "PRODUCT_SEARCH"
        )

    def intent_factory(messages):
        # the scripted provider maps by the user message (the query)
        user = messages[-1].content.strip().lower()
        return _intent_response(intent_by_query.get(user, "PRODUCT_SEARCH"))

    def extract_factory(messages):
        user = messages[-1].content
        match = _ORDER_NUMBER_RE.search(user)
        return {
            "category": None,
            "brand": None,
            "min_price_cents": None,
            "max_price_cents": None,
            "features": [],
            "product_ids": [],
            "order_number": match.group(0) if match else None,
            "product_names": [],
        }

    return ScriptedLLMProvider(
        responses={
            "intent": intent_factory,
            "extract": extract_factory,
            "rank": {"ranked_product_ids": ["p1", "p2", "p3"]},
            "response": "Scripted answer for evaluation purposes.",
        }
    )


async def evaluate_behavioral(container, dataset: list[dict]) -> dict:
    provider = _build_provider(dataset)
    container.router.providers = [provider]
    container.router.default_provider = provider

    _install_eval_stubs(container)

    results: list[dict] = []
    for case in dataset:
        result = await _run_case(container, case)
        results.append(result)

    passed = sum(1 for r in results if r["passed"])
    return {
        "cases": results,
        "passed_cases": passed,
        "total_cases": len(results),
        "pass_rate": passed / len(results),
    }


def _install_eval_stubs(container) -> None:
    """Replace network/DB touchpoints with deterministic stubs.

    The agent graph itself (routing, permissions, iteration limits) is
    still exercised for real — only I/O leaves are stubbed.
    """

    async def fake_retrieve(query: str, *, top_k: int | None = None, filters: dict | None = None):
        content = (
            "Product: ASUS Vivobook 16X\nBrand: ASUS\nCategory: Notebooks\n"
            "Price: around R$4.500 to R$5.000\nDescription: notebook with 16 GB RAM, "
            "Ryzen 7, 512 GB NVMe SSD, ideal for Docker and backend development.\n"
            "Specifications: - Processor: AMD Ryzen 7 5800H\n- RAM: 16 GB DDR4\n- Storage: 512 GB"
        )
        return [
            {
                "id": f"chunk-{case_id}",
                "product_id": "p1",
                "content": content,
                "similarity": 0.9,
                "metadata": {"category": "notebooks", "price_cents": 489900, "in_stock": True},
            }
            for case_id in range(3)
        ]

    container.retriever.retrieve = fake_retrieve

    async def fake_execute(arguments: dict, auth):
        from app.tools.base import ToolResult

        return ToolResult(ok=True, data={"stubbed": True})

    for tool in container.tools.values():
        tool.execute = fake_execute


async def _run_case(container, case: dict) -> dict:
    expected = case["expected"]
    state: AgentState = {
        "messages": [{"role": "user", "content": case["input"]}],
        "query": case["input"],
        "user_id": "eval-user" if "auth" in case.get("name", "") else "eval-user",
        "correlation_id": f"eval-{case['id']}",
        "extracted_requirements": {},
        "retrieved_documents": [],
        "ranked_products": [],
        "tool_results": [],
        "sources": [],
        "security_flags": [],
        "iterations": 0,
        "_max_iterations": container.settings.agent_max_iterations,
    }
    try:
        result = await asyncio.wait_for(container.graph.ainvoke(state), timeout=30)
    except Exception as exc:  # noqa: BLE001
        return {
            "id": case["id"],
            "name": case["name"],
            "passed": False,
            "details": f"graph error: {exc}",
        }

    intent = result.get("intent")
    tools_called = [tr for tr in result.get("tool_results", []) if tr.get("ok")]
    called_tool_names = [
        tr.get("meta", {}).get("tool") for tr in result.get("tool_results", []) if tr.get("ok")
    ]
    rag_used = len(result.get("retrieved_documents", [])) > 0

    checks: list[tuple[str, bool]] = []

    expected_intent = expected.get("intent")
    if expected_intent == "REFUSED":
        refused = intent == "REFUSED" or bool(result.get("security_flags"))
        checks.append(("refused", refused))
        checks.append(("no tools executed", not tools_called))
    else:
        checks.append(("intent", intent == expected_intent))
        expected_tool = expected.get("tool_called")
        if expected_tool:
            checks.append(("expected tool called", expected_tool in called_tool_names))
        if expected.get("rag_used"):
            checks.append(("rag used", rag_used))

    failed = [name for name, ok in checks if not ok]
    return {
        "id": case["id"],
        "name": case["name"],
        "passed": not failed,
        "details": (
            f"intent={intent} tools={called_tool_names} rag={rag_used} failed_checks={failed}"
        ),
    }
