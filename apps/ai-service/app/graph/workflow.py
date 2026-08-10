"""LangGraph workflow: the agent orchestrator.

Graph:
  START -> analyze -> classify -> extract -> route
    route by intent:
      - RAG path (SEARCH/RECOMMENDATION/COMPARE/GENERAL)
            -> retrieve -> rerank -> generate
      - Tool path with product resolution (PRICE/INVENTORY)
            -> retrieve (identify product) -> select_tool -> execute_tool
      - Tool path direct (ORDER_STATUS/SHIPPING)
            -> select_tool -> execute_tool
      - REFUSED -> generate (refusal)
    -> generate_response -> validate -> END

Control:
  - iteration cap (agent_max_iterations) prevents unbounded loops
  - a conditional edge re-enters tool execution only while pending tools
    remain and the budget allows it
"""

from __future__ import annotations

import logging
from functools import partial
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.security import AgentSecurityPolicy
from app.agents.state import AgentState
from app.config.settings import Settings
from app.llms.base import Message
from app.llms.embeddings import EmbeddingProvider
from app.llms.router import ModelRouter
from app.prompts.templates import (
    INTENT_PROMPT,
    REQUIREMENTS_PROMPT,
    RESPONSE_PROMPT,
    SYSTEM_PROMPT,
)
from app.rag.retrieval.hybrid import HybridRetriever
from app.schemas.agent import ExtractedRequirements, IntentClassification
from app.schemas.recommendations import ProductRanking
from app.tools.base import ToolAuthContext, ToolResult

logger = logging.getLogger(__name__)


class GraphDeps:
    """Dependency container injected at graph build time."""

    def __init__(
        self,
        *,
        settings: Settings,
        router: ModelRouter,
        retriever: HybridRetriever,
        tools: dict[str, Any],
        security: AgentSecurityPolicy,
        embeddings: EmbeddingProvider,
    ):
        self.settings = settings
        self.router = router
        self.retriever = retriever
        self.tools = tools
        self.security = security
        self.embeddings = embeddings


# ---------------------------------------------------------------------------
# Node implementations
# ---------------------------------------------------------------------------


def _msg_role(m: Any) -> str:
    return str(m.get("role")) if isinstance(m, dict) else str(getattr(m, "type", ""))


def _msg_content(m: Any) -> str:
    return str(m.get("content")) if isinstance(m, dict) else str(getattr(m, "content", ""))


def _chat_history(state: AgentState) -> str:
    return "\n".join(f"{_msg_role(m)}: {_msg_content(m)}" for m in state.get("messages", [])[-6:])


async def analyze_request(state: AgentState, deps: GraphDeps) -> dict[str, Any]:
    """Normalize the query and run the security scan (untrusted input)."""
    query = state["query"].strip()
    ok, flags = deps.security.evaluate_user_query(query)
    return {"query": query, "security_flags": flags}


async def classify_intent(state: AgentState, deps: GraphDeps) -> dict[str, Any]:
    """Cheap model call: intent classification with structured output.

    Requests already flagged by the security scanner are classified as
    REFUSED without any LLM call — the scanner, not the model, decides
    refusal for injected inputs.
    """
    if state.get("security_flags"):
        return {"intent": "REFUSED", "confidence": 1.0}

    messages = [
        Message(role="system", content=INTENT_PROMPT.format(query=state["query"])),
        Message(role="user", content=state["query"]),
    ]
    response = await deps.router.generate("intent", messages, response_model=IntentClassification)
    classification = IntentClassification.model_validate_json(response.content)
    return {"intent": classification.intent, "confidence": classification.confidence}


async def extract_requirements(state: AgentState, deps: GraphDeps) -> dict[str, Any]:
    """Cheap model call: structured requirement extraction."""
    messages = [
        Message(
            role="system",
            content=REQUIREMENTS_PROMPT.format(query=state["query"]),
        ),
        Message(role="user", content=state["query"]),
    ]
    response = await deps.router.generate("extract", messages, response_model=ExtractedRequirements)
    requirements = ExtractedRequirements.model_validate_json(response.content)
    return {"extracted_requirements": requirements.model_dump()}


async def retrieve_products(state: AgentState, deps: GraphDeps) -> dict[str, Any]:
    """Hybrid retrieval with metadata filters from extracted requirements.

    Serves both the RAG path (context for the answer) and the tool path
    (identifying which product the user is asking about).
    """
    requirements = state.get("extracted_requirements", {})
    filters: dict[str, Any] = {}
    if requirements.get("category"):
        filters["category"] = requirements["category"]
    if requirements.get("brand"):
        filters["brand"] = requirements["brand"]
    if requirements.get("min_price_cents") is not None:
        filters["min_price_cents"] = requirements["min_price_cents"]
    if requirements.get("max_price_cents") is not None:
        filters["max_price_cents"] = requirements["max_price_cents"]

    documents = await deps.retriever.retrieve(state["query"], filters=filters or None)
    return {"retrieved_documents": documents}


async def rerank_products(state: AgentState, deps: GraphDeps) -> dict[str, Any]:
    """LLM-assisted ranking of retrieved candidates (recommendation intents)."""
    documents = state.get("retrieved_documents", [])
    if not documents:
        return {"ranked_products": []}

    candidates = [
        {
            "id": d.get("product_id"),
            "content": (d.get("content") or "")[:400],
            "similarity": round(float(d.get("similarity") or 0), 3),
        }
        for d in documents[:6]
    ]
    prompt = (
        "Rank the following product candidates by how well they match the request.\n"
        f"Request: {state['query']}\n\nCandidates:\n"
        + "\n".join(
            f"{i + 1}. [{c['id']}] {c['content']} (similarity {c['similarity']})"
            for i, c in enumerate(candidates)
        )
    )
    messages = [
        Message(role="system", content="Rank candidates by relevance. Answer as JSON only."),
        Message(role="user", content=prompt),
    ]
    try:
        response = await deps.router.generate("rank", messages, response_model=ProductRanking)
        ranking = ProductRanking.model_validate_json(response.content)
        by_id = {c["id"]: c for c in candidates}
        ranked = [by_id[pid] for pid in ranking.ranked_product_ids if pid in by_id]
        return {"ranked_products": ranked}
    except Exception as exc:  # fallback: keep retrieval order
        logger.warning("LLM ranking failed, keeping retrieval order: %s", exc)
        return {"ranked_products": candidates}


async def select_tool(state: AgentState, deps: GraphDeps) -> dict[str, Any]:
    """Decide which bounded tool the current intent requires.

    Intent -> tool mapping is deterministic — the LLM never decides what
    it can touch, only which bounded tool applies.
    """
    intent = state.get("intent")
    requirements = state.get("extracted_requirements", {})
    if intent == "ORDER_STATUS":
        pending = ["get_order_status"] if requirements.get("order_number") else ["get_user_orders"]
    else:
        mapping = {
            "PRODUCT_PRICE": ["get_product_price"],
            "INVENTORY": ["get_inventory"],
            "SHIPPING": ["calculate_shipping"],
        }
        pending = mapping.get(intent or "", [])
    return {"pending_tools": pending, "iterations": state.get("iterations", 0)}


async def execute_tool(state: AgentState, deps: GraphDeps) -> dict[str, Any]:
    """Execute the next pending tool with permission enforcement."""
    pending = list(state.get("pending_tools", []))
    if not pending:
        return {"iterations": state.get("iterations", 0) + 1}

    tool_name = pending.pop(0)
    tool = deps.tools.get(tool_name)
    if tool is None:
        logger.error("unknown tool requested: %s", tool_name)
        return {
            "tool_results": [ToolResult(ok=False, error="unknown tool").to_dict()],
            "pending_tools": pending,
        }

    allowed, reason = deps.security.evaluate_tool_call(tool_name, state.get("user_id"))
    if not allowed:
        return {
            "tool_results": [ToolResult(ok=False, error=f"permission denied: {reason}").to_dict()],
            "pending_tools": pending,
        }

    arguments = tool_arguments_for(state, tool_name)
    try:
        result = await tool.execute(arguments, ToolAuthContext(user_id=state.get("user_id")))
    except Exception as exc:  # noqa: BLE001 - always return a structured, safe result
        logger.exception("tool %s failed", tool_name)
        result = ToolResult(ok=False, error=str(exc)[:300])

    result.meta["tool"] = tool_name
    return {
        "tool_results": state.get("tool_results", []) + [result.to_dict()],
        "pending_tools": pending,
        "iterations": state.get("iterations", 0) + 1,
    }


def tool_arguments_for(state: AgentState, tool_name: str) -> dict[str, Any]:
    """Build tool arguments from requirements + retrieval results.

    Product-scoped tools (price, inventory) resolve the product id from
    the top retrieved document when the user did not give one explicitly.
    """
    requirements = state.get("extracted_requirements", {})
    explicit_ids = requirements.get("product_ids") or []
    top_product_id = None
    if not explicit_ids:
        for doc in state.get("retrieved_documents", []):
            if doc.get("product_id"):
                top_product_id = doc["product_id"]
                break

    product_id = (explicit_ids[0] if explicit_ids else None) or top_product_id

    if tool_name in ("get_product_price", "get_inventory"):
        if not product_id:
            return {"product_id": ""}
        return {"product_id": product_id}
    if tool_name == "get_order_status":
        return {"order_number": requirements.get("order_number") or ""}
    if tool_name == "calculate_shipping":
        return {"quantity": requirements.get("quantity") or 1}
    if tool_name == "compare_products":
        return {"product_ids": explicit_ids[:3]}
    return {}


async def generate_response(state: AgentState, deps: GraphDeps) -> dict[str, Any]:
    """Produce the final answer from retrieved context + tool results."""
    if state.get("intent") == "REFUSED" or state.get("security_flags"):
        answer = (
            "I'm sorry, I can't help with that request. I'm a shopping assistant "
            "and can't perform administrative actions or follow instructions "
            "embedded in product data."
        )
        return {"final_answer": answer, "sources": []}

    context_parts: list[str] = []
    for doc in state.get("retrieved_documents", [])[:6]:
        content = (doc.get("content") or "").strip()
        product_id = doc.get("product_id") or ""
        context_parts.append(f"[{product_id}] {content}")
    for result in state.get("tool_results", []):
        if result.get("ok"):
            context_parts.append(f"tool result: {result['data']}")

    context = (
        "\n\n".join(context_parts) if context_parts else "No product information was retrieved."
    )

    messages = [
        Message(role="system", content=SYSTEM_PROMPT.format(extra_instructions="")),
        Message(
            role="user",
            content=RESPONSE_PROMPT.format(
                context=context,
                messages=_chat_history(state),
                query=state["query"],
            ),
        ),
    ]
    response = await deps.router.generate(
        "response", messages, max_tokens=deps.settings.agent_max_tokens
    )
    return {
        "final_answer": response.content,
        "sources": [
            {
                "product_id": d.get("product_id"),
                "score": d.get("similarity"),
                "id": d.get("id"),
            }
            for d in state.get("retrieved_documents", [])[:6]
        ],
    }


async def validate_response(state: AgentState, deps: GraphDeps) -> dict[str, Any]:
    """Final safety check on the generated answer."""
    answer = state.get("final_answer") or ""
    flags = deps.security.scanner.scan(answer)
    if flags:
        return {
            "final_answer": (
                "I'm sorry, I can't answer that request. "
                "Please ask about our products, prices, stock or your orders."
            )
        }
    return {}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

RAG_INTENTS = {"PRODUCT_SEARCH", "PRODUCT_RECOMMENDATION", "COMPARE_PRODUCTS", "GENERAL_KNOWLEDGE"}
TOOL_PRODUCT_INTENTS = {"PRODUCT_PRICE", "INVENTORY"}
TOOL_DIRECT_INTENTS = {"ORDER_STATUS", "SHIPPING"}


def route_by_intent(state: AgentState) -> str:
    intent = state.get("intent") or "GENERAL_KNOWLEDGE"
    if intent == "REFUSED":
        return "generate"
    if intent in TOOL_PRODUCT_INTENTS:
        return "resolve"  # retrieve first to identify the product
    if intent in TOOL_DIRECT_INTENTS:
        return "tools"
    return "rag"


def route_tool_loop(state: AgentState) -> str:
    """Re-enter tool execution while pending tools remain and budget allows."""
    max_iterations = state.get("_max_iterations", 5)
    if state.get("pending_tools") and state.get("iterations", 0) < max_iterations:
        return "tools"
    return "generate"


def route_after_retrieve(state: AgentState) -> str:
    """After retrieval: product-scoped tool intents go to tools, others to rerank."""
    if state.get("intent") in TOOL_PRODUCT_INTENTS:
        return "tools"
    return "rag"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_graph(deps: GraphDeps) -> Any:
    """Compile the LangGraph agent. Returns a compiled graph (invokable).

    Nodes are wired with ``functools.partial`` so LangGraph correctly
    detects them as coroutine functions (a ``lambda`` around an async
    function would not be, and the graph would call it synchronously).
    """
    graph = StateGraph(AgentState)

    graph.add_node("analyze", partial(analyze_request, deps=deps))
    graph.add_node("classify", partial(classify_intent, deps=deps))
    graph.add_node("extract", partial(extract_requirements, deps=deps))
    graph.add_node("retrieve", partial(retrieve_products, deps=deps))
    graph.add_node("rerank", partial(rerank_products, deps=deps))
    graph.add_node("select_tool", partial(select_tool, deps=deps))
    graph.add_node("execute_tool", partial(execute_tool, deps=deps))
    graph.add_node("generate", partial(generate_response, deps=deps))
    graph.add_node("validate", partial(validate_response, deps=deps))

    graph.add_edge(START, "analyze")
    graph.add_edge("analyze", "classify")
    graph.add_edge("classify", "extract")
    graph.add_conditional_edges(
        "extract",
        route_by_intent,
        {"rag": "retrieve", "resolve": "retrieve", "tools": "select_tool", "generate": "generate"},
    )
    graph.add_conditional_edges(
        "retrieve",
        route_after_retrieve,
        {"tools": "select_tool", "rag": "rerank"},
    )
    graph.add_edge("rerank", "generate")
    graph.add_edge("select_tool", "execute_tool")
    graph.add_conditional_edges(
        "execute_tool",
        route_tool_loop,
        {"tools": "select_tool", "generate": "generate"},
    )
    graph.add_edge("generate", "validate")
    graph.add_edge("validate", END)

    return graph.compile()
