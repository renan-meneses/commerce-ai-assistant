"""Chat endpoint: the agent's public API."""

from __future__ import annotations

import logging
import time
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app.agents.state import AgentState
from app.api.dependencies import AgentContainer, get_container

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


class ChatMessage(BaseModel):
    role: str = Field(description="user | assistant")
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)
    user_id: str | None = None
    correlation_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    intent: str
    confidence: float = 0.0
    sources: list[dict[str, Any]] = Field(default_factory=list)
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    trace_id: str | None = None
    latency_ms: float = 0.0


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    container: Annotated[AgentContainer, Depends(get_container)],
    x_request_id: Annotated[str | None, Header()] = None,
) -> ChatResponse:
    started = time.monotonic()
    correlation_id = payload.correlation_id or x_request_id or ""
    query = payload.messages[-1].content if payload.messages else ""

    if not query.strip():
        raise HTTPException(status_code=400, detail="last message must not be empty")

    initial_state: AgentState = {
        "messages": [m.model_dump() for m in payload.messages],
        "query": query,
        "user_id": payload.user_id,
        "correlation_id": correlation_id,
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
        result: dict[str, Any] = await container.graph.ainvoke(initial_state)
    except Exception as exc:
        logger.exception("agent invocation failed for correlation %s", correlation_id)
        raise HTTPException(status_code=500, detail="agent execution failed") from exc

    latency_ms = round((time.monotonic() - started) * 1000, 1)
    return ChatResponse(
        answer=result.get("final_answer") or "Sorry, I could not answer that.",
        intent=result.get("intent") or "UNKNOWN",
        confidence=float(result.get("confidence") or 0.0),
        sources=result.get("sources", []),
        tool_results=result.get("tool_results", []),
        trace_id=correlation_id or None,
        latency_ms=latency_ms,
    )
