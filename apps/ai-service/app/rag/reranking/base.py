"""Reranker abstraction.

Retrieval depends on this interface — not on a specific implementation.
SimpleScoreReranker is the default; provider-based rerankers (e.g. an
LLM or a cross-encoder API) can be swapped in without touching retrieval.
"""

from __future__ import annotations

from typing import Any, Protocol

from langchain_core.documents import Document


class Reranker(Protocol):
    async def rerank(
        self,
        query: str,
        documents: list[Document],
    ) -> list[Document]: ...

    async def rerank_dicts(
        self,
        query: str,
        items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]: ...
