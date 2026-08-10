"""RAG pipeline facade: query -> retrieval -> context (with tracing hooks)."""

from __future__ import annotations

from typing import Any

from app.config.settings import Settings
from app.rag.retrieval.hybrid import HybridRetriever


class RagPipeline:
    """High-level RAG entry point used by the agent and the eval CLI."""

    def __init__(self, retriever: HybridRetriever, settings: Settings):
        self.retriever = retriever
        self.settings = settings

    async def retrieve(
        self,
        query: str,
        *,
        top_k: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return await self.retriever.retrieve(
            query,
            top_k=top_k or self.settings.retrieval_top_k,
            filters=filters,
        )

    async def context(
        self,
        query: str,
        *,
        top_k: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> str:
        documents = await self.retrieve(query, top_k=top_k, filters=filters)
        return "\n\n".join(f"[{d.get('product_id')}] {d.get('content')}" for d in documents)
