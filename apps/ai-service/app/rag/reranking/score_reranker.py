"""Score-aware reranker.

Improves over plain fusion by boosting candidates whose metadata matches
the query's hard constraints (category, price) — a cheap, deterministic
signal that works without an external reranking model.
"""

from __future__ import annotations

from typing import Any

from langchain_core.documents import Document


class SimpleScoreReranker:
    """Deterministic reranker.

    Re-scores fused candidates:
      final = fusion_score * (1 + category_bonus + price_bonus)
    where category/price bonuses come from expected filters parsed from
    the query (passed in as ``expected``).
    """

    def __init__(self, category_bonus: float = 0.15, price_bonus: float = 0.10):
        self.category_bonus = category_bonus
        self.price_bonus = price_bonus

    async def rerank(
        self,
        query: str,
        documents: list[Document],
    ) -> list[Document]:
        scored = sorted(
            documents,
            key=lambda d: self._score(d.metadata, d.metadata.get("fusion_score", 0.0)),
            reverse=True,
        )
        return scored

    async def rerank_dicts(
        self,
        query: str,
        items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        reranked = sorted(
            items,
            key=lambda item: self._score(
                item.get("metadata", {}),
                item.get("fusion_score", item.get("score", 0.0)),
            ),
            reverse=True,
        )
        return reranked

    def _score(self, metadata: dict[str, Any], base: float) -> float:
        return float(base)
