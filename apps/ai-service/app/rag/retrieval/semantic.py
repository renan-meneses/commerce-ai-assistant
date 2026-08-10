"""Semantic retrieval: embed query -> pgvector cosine search."""

from __future__ import annotations

from typing import Any

from app.config.settings import Settings
from app.llms.embeddings import EmbeddingProvider
from app.rag.store.pgvector_store import PgVectorStore


class SemanticRetriever:
    def __init__(
        self,
        store: PgVectorStore,
        embeddings: EmbeddingProvider,
        settings: Settings,
    ):
        self.store = store
        self.embeddings = embeddings
        self.settings = settings

    async def search(
        self,
        query: str,
        *,
        top_k: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        query_vector = await self.embeddings.embed_query(query)
        return await self.store.semantic_search(
            query_vector,
            model=self.embeddings.model_name,
            top_k=top_k or self.settings.retrieval_top_k,
            filters=filters,
        )
