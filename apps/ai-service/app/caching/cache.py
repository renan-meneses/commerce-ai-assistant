"""Redis-backed cache with per-domain TTL policies.

TTL policy (documented in docs/rag-architecture.md):
- product catalog data            -> long TTL  (1h)
- semantic search results         -> medium TTL (5m)
- prices                         -> short TTL (30s)
- inventory                      -> NO cache (live truth)

Nothing is cached indiscriminately: hot reads (catalog, searches) get
cached; volatile or auth-scoped data (stock, order status) does not.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.config.settings import Settings

logger = logging.getLogger(__name__)


class CacheService:
    """Async Redis cache. Gracefully degrades to no-op if Redis is down."""

    def __init__(self, settings: Settings):
        self._redis: aioredis.Redis | None = aioredis.from_url(
            settings.redis_url, decode_responses=True
        )
        self._available = True

    async def get(self, key: str, ttl: int | None = None) -> Any | None:
        del ttl  # read-through TTL is enforced at write time
        if not self._available or self._redis is None:
            return None
        try:
            raw = await self._redis.get(key)
            return json.loads(raw) if raw else None
        except Exception as exc:  # pragma: no cover - depends on infra state
            logger.warning("cache get failed: %s", exc)
            return None

    async def set(self, key: str, value: Any, ttl: int) -> None:
        if not self._available or self._redis is None or ttl <= 0:
            return
        try:
            await self._redis.set(key, json.dumps(value, default=str), ex=ttl)
        except Exception as exc:  # pragma: no cover
            logger.warning("cache set failed: %s", exc)

    async def delete(self, key: str) -> None:
        if not self._available or self._redis is None:
            return
        try:
            await self._redis.delete(key)
        except Exception as exc:  # pragma: no cover
            logger.warning("cache delete failed: %s", exc)

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
