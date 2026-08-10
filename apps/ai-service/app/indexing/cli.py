"""Reindex CLI: `python -m app.rag.indexing.cli --reindex-all` (via Makefile)."""

from __future__ import annotations

import argparse
import asyncio
import logging

from app.config.settings import get_settings
from app.indexing.indexer import ProductIndexer
from app.llms.embeddings import build_embedding_provider
from app.rag.store.pgvector_store import PgVectorStore
from app.tools.commerce_client import CommerceClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")


async def reindex_all(page_size: int = 50) -> None:
    settings = get_settings()
    store = PgVectorStore(settings)
    embeddings = build_embedding_provider(settings)
    indexer = ProductIndexer(store, embeddings)
    client = CommerceClient(settings)

    page = 1
    total_indexed = 0
    try:
        while True:
            payload = await client.list_products(
                {"limit": page_size, "page": page, "sortBy": "createdAt"}
            )
            items = payload.get("items", [])
            if not items:
                break
            for item in items:
                product = await client.get_product(item["id"])
                count = await indexer.index_product(product)
                total_indexed += count
            total = payload.get("total", 0)
            print(f"page {page}: indexed {len(items)} products (total so far: {total_indexed})")
            if page * page_size >= total:
                break
            page += 1
    finally:
        await client.close()
        await store.close()

    print(f"Reindex complete: {total_indexed} chunks written.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG indexing utilities")
    parser.add_argument("--reindex-all", action="store_true", help="Re-index the whole catalog")
    args = parser.parse_args()
    if args.reindex_all:
        asyncio.run(reindex_all())
    else:
        parser.print_help()
