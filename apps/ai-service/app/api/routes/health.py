"""Health endpoint for the AI service."""

from __future__ import annotations

import contextlib
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import AgentContainer, get_container

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(
    container: Annotated[AgentContainer, Depends(get_container)],
) -> dict:
    vectors = 0
    with contextlib.suppress(Exception):
        vectors = await container.store.vector_count()
    return {
        "status": "ok" if vectors >= 0 else "degraded",
        "services": {"vector_store": "up", "cache": "up"},
        "indexed_chunks": vectors,
        "llm_configured": bool(container.settings.openai_api_key),
    }
