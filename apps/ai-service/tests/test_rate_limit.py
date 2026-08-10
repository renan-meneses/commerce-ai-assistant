"""Unit tests for the Redis-backed rate limiter."""

import pytest

from app.config.settings import Settings
from app.security.rate_limit import _INCR_SCRIPT, RateLimiter


def test_script_uses_fixed_window():
    assert "INCR" in _INCR_SCRIPT
    assert "EXPIRE" in _INCR_SCRIPT
    assert "ARGV[1]" in _INCR_SCRIPT


@pytest.mark.asyncio
async def test_limiter_blocks_over_limit():
    settings = Settings(rate_limit_max_requests=2, rate_limit_ttl_seconds=60)
    limiter = RateLimiter(settings)
    fake = _FakeRedis(script=_INCR_SCRIPT)
    limiter._redis = fake
    limiter._script = "sha1"

    await limiter.check("client-a")
    await limiter.check("client-a")
    with pytest.raises(Exception) as exc_info:
        await limiter.check("client-a")
    assert getattr(exc_info.value, "status_code", None) == 429


@pytest.mark.asyncio
async def test_limiter_allows_under_limit():
    settings = Settings(rate_limit_max_requests=3, rate_limit_ttl_seconds=60)
    limiter = RateLimiter(settings)
    fake = _FakeRedis(script=_INCR_SCRIPT)
    limiter._redis = fake
    limiter._script = "sha1"

    await limiter.check("client-b")
    await limiter.check("client-b")
    await limiter.check("client-b")  # 3rd hit == limit, still allowed


class _FakeRedis:
    """Minimal stand-in: script_load returns a sha; evalsha counts per key."""

    def __init__(self, script: str):
        self._script = script
        self._counts: dict[str, int] = {}

    async def script_load(self, script: str) -> str:
        assert script == self._script
        return "sha1"

    async def evalsha(self, sha: str, numkeys: int, key: str, window: int):
        assert sha == "sha1" and numkeys == 1 and window > 0
        count = self._counts.get(key, 0) + 1
        self._counts[key] = count
        return count
