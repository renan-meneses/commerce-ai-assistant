"""RabbitMQ indexing consumer.

Consumes product.created/product.updated events, fetches the product
from the commerce API, and runs the indexing pipeline.

Failure handling:
- retriable failures (transient network/DB) -> reject with requeue=false
  so the message goes to the dead-letter queue (commerce.product.dlx);
- the DLQ is surfaced via the management UI; a re-drive script re-publishes
  DLQ messages (scripts/requeue_dlq.py).

Idempotency: replaying an event converges to the same final state
(deterministic chunk ids + delete-before-upsert), so the worker can be
re-run freely.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import aio_pika

from app.config.settings import Settings
from app.indexing.indexer import ProductIndexer

logger = logging.getLogger(__name__)

QUEUE = "commerce.indexing.product"


class IndexingWorker:
    def __init__(
        self,
        settings: Settings,
        indexer: ProductIndexer,
        product_fetcher: Any,
    ):
        self.settings = settings
        self.indexer = indexer
        self.product_fetcher = product_fetcher

    async def run(self) -> None:
        connection = await aio_pika.connect_robust(self.settings.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=4)
            queue = await channel.declare_queue(
                QUEUE,
                durable=True,
                arguments={"x-dead-letter-exchange": "commerce.product.dlx"},
            )
            await queue.bind("commerce.product", "product.*")
            logger.info("indexing worker listening on %s", QUEUE)
            async with queue.iterator() as messages:
                async for message in messages:
                    await self.handle(message)

    async def handle(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        async with message.process(requeue=False, reject_on_redelivered=True):
            try:
                event = json.loads(message.body)
                product_id = event.get("productId")
                if not product_id:
                    logger.warning("dropping malformed event: %s", message.body[:200])
                    return
                product = await self.product_fetcher(product_id)
                if product is None:
                    logger.warning("product %s not found for indexing", product_id)
                    return
                await self.indexer.index_product(product)
                logger.info("indexed product %s from event", product_id)
            except Exception as exc:  # noqa: BLE001 - DLQ on any failure
                logger.exception("indexing failed; routing to DLQ: %s", exc)
                raise


async def run_worker(settings: Settings, indexer: ProductIndexer, fetcher: Any) -> None:
    worker = IndexingWorker(settings, indexer, fetcher)
    await worker.run()
