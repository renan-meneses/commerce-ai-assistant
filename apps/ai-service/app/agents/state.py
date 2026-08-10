"""LangGraph agent state."""

from __future__ import annotations

from typing import Annotated, Any, Literal, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    # conversational
    messages: Annotated[list[dict[str, str]], add_messages]

    # context
    user_id: str | None
    correlation_id: str | None

    # analysis
    query: str
    intent: str | None
    confidence: float
    extracted_requirements: dict[str, Any]

    # retrieval
    retrieved_documents: list[dict[str, Any]]
    ranked_products: list[dict[str, Any]]

    # tools
    tool_results: list[dict[str, Any]]
    pending_tools: list[str]

    # output
    final_answer: str | None
    sources: list[dict[str, Any]]
    trace_id: str | None

    # control
    iterations: int
    security_flags: list[str]
    _max_iterations: int


Intent = Literal[
    "PRODUCT_SEARCH",
    "PRODUCT_RECOMMENDATION",
    "COMPARE_PRODUCTS",
    "PRODUCT_PRICE",
    "INVENTORY",
    "ORDER_STATUS",
    "SHIPPING",
    "GENERAL_KNOWLEDGE",
    "REFUSED",
]
