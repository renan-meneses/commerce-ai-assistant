"""LLM provider abstraction.

The agent domain layer depends only on these protocols — never on a
specific vendor SDK. Adapters (OpenAI today, Anthropic/Gemini/OpenRouter
later) implement them behind the same interface (ADR-007).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    content: str
    raw: Any = None
    usage: dict = field(default_factory=dict)
    provider: str = ""
    model: str = ""
    latency_ms: float = 0.0


@runtime_checkable
class LLMProvider(Protocol):
    """A chat-completion provider that can optionally return structured output."""

    provider_name: str

    async def generate(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        response_model: type[BaseModel] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        callbacks: list | None = None,
    ) -> LLMResponse:
        """Generate a completion.

        When ``response_model`` is given, the provider must validate the
        output against the Pydantic model before returning it and raise
        ``LLMValidationError`` on failure.
        """
        ...


class LLMError(Exception):
    """Raised when a provider fails to produce a usable response."""


class LLMValidationError(LLMError):
    """Raised when structured output fails schema validation."""
