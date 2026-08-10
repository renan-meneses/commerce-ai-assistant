"""Redis-backed fixed-window rate limiting for the AI chat endpoint.

The NestJS API already rate-limits inbound HTTP (60 req/min per client).
The AI service adds its own guard so the agent (the most expensive path,
LLM + retrieval) cannot be hammered directly or through a misconfigured
proxy. Limits are per user id (when available) else per client IP, using
a fixed window: `INCR` + `EXPIRE` in a small Lua script.

Degrades to allow when Redis is down (fail-open keeps chat available).
"""

from __future__ import annotations

import logging
from functools import lru_cache

import redis.asyncio as aioredis
from fastapi import HTTPException, Request

from app.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)

# Lua: increment + set TTL on first hit, return current count atomically.
_INCR_SCRIPT = """
local c = redis.call('INCR', KEYS[1])
if c == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return c
"""


class RateLimiter:
    def __init__(self, settings: Settings):
        self._redis: aioredis.Redis | None = aioredis.from_url(
            settings.redis_url, decode_responses=True
        )
        self._limit = settings.rate_limit_max_requests
        self._window = settings.rate_limit_ttl_seconds
        self._script: str | None = None

    async def check(self, client_key: str) -> None:
        """Raise 429 when the client exceeds the window limit."""
        if self._redis is None:
            return
        try:
            if self._script is None:
                self._script = await self._redis.script_load(_INCR_SCRIPT)
            key = f"ratelimit:{client_key}"
            count = await self._redis.evalsha(self._script, 1, key, self._window)
        except Exception as exc:  # pragma: no cover - infra dependent
            logger.warning("rate limiter unavailable, failing open: %s", exc)
            return
        if int(count) > self._limit:
            raise HTTPException(
                status_code=429,
                detail="rate limit exceeded, try again later",
                headers={"Retry-After": str(self._window)},
            )


@lru_cache
def get_limiter() -> RateLimiter:
    return RateLimiter(get_settings())


async def enforce_rate_limit(request: Request) -> None:
    """FastAPI dependency: one token per request for the AI chat endpoint."""
    client_key = request.headers.get("x-user-id") or (
        request.client.host if request.client else "unknown"
    )
    await get_limiter().check(client_key)
