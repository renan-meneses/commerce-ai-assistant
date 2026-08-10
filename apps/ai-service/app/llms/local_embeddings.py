"""Local embedding fallback (sentence-transformers) for offline use.

Not used in production; exists so the whole RAG pipeline can run in CI
and local demos without an API key (see docs/rag-architecture.md).
"""

from __future__ import annotations

from app.config.settings import Settings


class LocalEmbeddingAdapter:
    model_name: str
    dimensions: int

    def __init__(self, settings: Settings):
        self.model_name = settings.embeddings_local_model
        self._model = None
        self.dimensions = 384  # bge-small-en-v1.5

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            self.dimensions = int(self._model.get_sentence_embedding_dimension())
        return self._model

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        import asyncio

        model = self._load()
        return await asyncio.to_thread(
            lambda: model.encode(texts, normalize_embeddings=True).tolist()
        )

    async def embed_query(self, text: str) -> list[float]:
        return (await self.embed_documents([text]))[0]
