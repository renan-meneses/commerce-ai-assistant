"""Langfuse integration for LLM observability.

Tracks: user request, intent, retrieval results, reranking, tool calls,
prompts, provider/model, tokens, latency and the final answer.
Content masking is applied to prompts/responses before they are logged
when LANGfuse masking is enabled (see app/security/masking.py).

Langfuse complements Prometheus/Grafana: metrics show *what* is
happening, traces show *why* (per-LLM-call reasoning).
"""

from __future__ import annotations

import logging
from typing import Any

from app.config.settings import Settings
from app.security.masking import mask_sensitive

logger = logging.getLogger(__name__)

_handler: Any | None = None


def get_langfuse_handler(settings: Settings) -> Any | None:
    """Return the Langfuse callback handler (or None when disabled)."""
    global _handler
    if _handler is not None:
        return _handler
    if not settings.langfuse_enabled:
        return None
    try:
        from langfuse.callback import CallbackHandler

        _handler = CallbackHandler(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
        logger.info("Langfuse tracing enabled (host=%s)", settings.langfuse_host)
    except Exception as exc:  # pragma: no cover
        logger.warning("Langfuse init failed: %s", exc)
        _handler = None
    return _handler


def masked(*, prompt: str, response: str, **extra: Any) -> dict[str, Any]:
    """Build a masked trace payload (never log secrets or PII verbatim)."""
    return {
        "prompt": mask_sensitive(prompt),
        "response": mask_sensitive(response),
        **extra,
    }
