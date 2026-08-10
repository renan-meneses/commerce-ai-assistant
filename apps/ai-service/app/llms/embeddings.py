"""Embedding provider abstraction + OpenAI/local/hash adapters."""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol, runtime_checkable

from langchain_openai import OpenAIEmbeddings

from app.config.settings import Settings


@runtime_checkable
class EmbeddingProvider(Protocol):
    model_name: str
    dimensions: int

    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    async def embed_query(self, text: str) -> list[float]: ...


class OpenAIEmbeddingAdapter:
    model_name: str
    dimensions: int

    def __init__(self, settings: Settings):
        self.model_name = settings.openai_embedding_model
        self.dimensions = settings.embedding_dimensions
        kwargs: dict = {
            "model": self.model_name,
            "api_key": settings.openai_api_key or "missing-key",
        }
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        self._client = OpenAIEmbeddings(**kwargs)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._client.aembed_documents(texts)

    async def embed_query(self, text: str) -> list[float]:
        return await self._client.aembed_query(text)


class HashEmbeddingAdapter:
    """Deterministic, dependency-free embeddings for offline dev/CI.

    A word-hash bag-of-words vector with feature hashing (signed sums),
    L2-normalized. Only measures lexical overlap — never use in
    production, where OpenAI (or a local sentence-transformer) is used.
    """

    model_name: str
    dimensions: int

    def __init__(self, settings: Settings):
        self.model_name = "hash-bow-v1"
        self.dimensions = settings.embedding_dimensions

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return re.findall(r"[a-z0-9]{2,}", text.lower())

    def _vector(self, text: str) -> list[float]:
        vec = [0.0] * self.dimensions
        for token in self._tokens(text):
            digest = hashlib.sha256(token.encode()).digest()
            index = int.from_bytes(digest[:4], "little") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[index] += sign
        norm = math.sqrt(sum(v * v for v in vec))
        if norm:
            vec = [v / norm for v in vec]
        return vec

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    async def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.embeddings_use_hash:
        return HashEmbeddingAdapter(settings)
    if settings.embeddings_use_local:
        # Local SentenceTransformer fallback for offline dev/CI.
        from app.llms.local_embeddings import LocalEmbeddingAdapter

        return LocalEmbeddingAdapter(settings)
    return OpenAIEmbeddingAdapter(settings)
