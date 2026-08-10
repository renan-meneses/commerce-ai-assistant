"""Worker process entrypoint: `python -m app.indexing.worker_main`."""

from __future__ import annotations

import asyncio
import logging

from app.config.settings import get_settings
from app.indexing.consumer import IndexingWorker
from app.indexing.indexer import ProductIndexer
from app.llms.embeddings import build_embedding_provider
from app.rag.store.pgvector_store import PgVectorStore
from app.tools.commerce_client import CommerceClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


async def fetch_product(product_id: str) -> dict | None:
    client = CommerceClient(get_settings())
    try:
        return await client.get_product(product_id)
    except Exception:
        return None
    finally:
        await client.close()


async def main() -> None:
    settings = get_settings()
    store = PgVectorStore(settings)
    embeddings = build_embedding_provider(settings)
    indexer = ProductIndexer(store, embeddings)
    worker = IndexingWorker(settings, indexer, fetch_product)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
