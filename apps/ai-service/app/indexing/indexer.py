"""Product indexer: build document -> chunk -> embed -> upsert (idempotent).

Idempotency strategy (documented in docs/rag-architecture.md):
- chunk ids are deterministic: sha256(product_id:version:doc_type:index)
- upserts use ON CONFLICT (id) DO UPDATE, so replaying an event
  overwrites the same rows instead of inserting duplicates
- before indexing a new product version, old rows for that product are
  removed, keeping exactly one copy of every (product, version) chunk
"""

from __future__ import annotations

import logging

from app.llms.embeddings import EmbeddingProvider
from app.rag.chunking.product_chunker import ProductChunker
from app.rag.documents.builder import ProductDocumentBuilder
from app.rag.store.pgvector_store import PgVectorStore

logger = logging.getLogger(__name__)


class ProductIndexer:
    def __init__(
        self,
        store: PgVectorStore,
        embeddings: EmbeddingProvider,
        builder: ProductDocumentBuilder | None = None,
        chunker: ProductChunker | None = None,
    ):
        self.store = store
        self.embeddings = embeddings
        self.builder = builder or ProductDocumentBuilder()
        self.chunker = chunker or ProductChunker()

    async def index_product(self, product: dict) -> int:
        """Index one product (full pipeline). Returns number of vectors written."""
        doc = self.builder.build(product)
        chunks = self.chunker.chunk(doc)

        # Replacing the product's old vectors keeps the store free of
        # stale versions and makes re-processing safe.
        await self.store.delete_product_vectors(doc.product_id)

        texts = [c.content for c in chunks]
        vectors = await self.embeddings.embed_documents(texts)

        records = [
            {
                "id": chunk.id,
                "product_id": chunk.product_id,
                "chunk_id": chunk.id,
                "content": chunk.content,
                "metadata": chunk.metadata,
                "vector": vectors[i],
            }
            for i, chunk in enumerate(chunks)
        ]
        written = await self.store.upsert_chunk_vectors(self.embeddings.model_name, records)
        logger.info(
            "indexed product %s v%d (%d chunks)",
            doc.product_id,
            doc.version,
            written,
        )
        return written
