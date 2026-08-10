"""Lexical (keyword) retrieval using PostgreSQL full-text search.

FTS over the stored content text; ts_rank provides the score used by
the fusion layer (RRF needs only ranks, but keeping the score lets us
support score-based fusion too).
"""

from __future__ import annotations

from typing import Any

from app.rag.store.pgvector_store import PgVectorStore


class KeywordRetriever:
    def __init__(self, store: PgVectorStore):
        self.store = store

    async def search(
        self,
        query: str,
        *,
        top_k: int = 6,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return await self.store.keyword_search(
            query,
            top_k=top_k,
            filters=filters,
        )
