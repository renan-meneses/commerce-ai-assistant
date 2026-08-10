"""Hybrid retrieval: semantic + keyword -> fusion -> rerank."""

from __future__ import annotations

from typing import Any

from app.config.settings import Settings
from app.rag.reranking.base import Reranker
from app.rag.retrieval.fusion import reciprocal_rank_fusion
from app.rag.retrieval.keyword import KeywordRetriever
from app.rag.retrieval.semantic import SemanticRetriever


class HybridRetriever:
    """Composes semantic and lexical search.

    Query pipeline: user question -> embedding -> vector search
    (semantic) + FTS (keyword) -> RRF fusion -> reranking -> top N.
    """

    def __init__(
        self,
        semantic: SemanticRetriever,
        keyword: KeywordRetriever,
        reranker: Reranker,
        settings: Settings,
    ):
        self.semantic = semantic
        self.keyword = keyword
        self.reranker = reranker
        self.settings = settings

    async def retrieve(
        self,
        query: str,
        *,
        top_k: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        top_k = top_k or self.settings.retrieval_top_k
        candidates = self.settings.retrieval_candidates

        semantic_results = await self.semantic.search(query, top_k=candidates, filters=filters)
        keyword_results = await self.keyword.search(query, top_k=candidates, filters=filters)

        fused = reciprocal_rank_fusion([semantic_results, keyword_results])
        reranked = await self.reranker.rerank_dicts(query, fused[: top_k * 2])
        return reranked[:top_k]
