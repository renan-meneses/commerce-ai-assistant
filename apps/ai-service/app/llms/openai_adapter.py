"""OpenAI-compatible LLM adapter (also covers OpenRouter via base URL)."""

from __future__ import annotations

import time
from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ValidationError

from app.config.settings import Settings
from app.llms.base import LLMError, LLMResponse, LLMValidationError, Message


class OpenAIAdapter:
    """Chat completion via OpenAI (or any OpenAI-compatible endpoint).

    Structured output is requested natively by the OpenAI API (JSON
    schema mode) and then re-validated with Pydantic locally — the LLM
    output is untrusted until it passes schema validation.
    """

    provider_name = "openai"

    def __init__(self, settings: Settings):
        kwargs: dict[str, Any] = {
            "model": settings.openai_model_chat,
            "api_key": settings.openai_api_key or "missing-key",
            "temperature": 0.0,
        }
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        self._client = ChatOpenAI(**kwargs)
        self._default_model = settings.openai_model_chat
        self._strong_model = settings.openai_model_strong

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
        started = time.monotonic()
        model_name = model or self._default_model
        try:
            config: RunnableConfig | None = {"callbacks": callbacks} if callbacks else None
            if response_model is not None:
                structured = self._client.with_structured_output(response_model)
                result = await structured.ainvoke(self._to_langchain(messages), config=config)
                validated = (
                    result
                    if isinstance(result, response_model)
                    else response_model.model_validate(result)
                )
                usage = getattr(result, "__dict__", {}).get("usage", {}) or {}
                return LLMResponse(
                    content=validated.model_dump_json(),
                    raw=validated,
                    usage=usage,
                    provider=self.provider_name,
                    model=model_name,
                    latency_ms=(time.monotonic() - started) * 1000,
                )

            result = await self._client.ainvoke(
                self._to_langchain(messages),
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                config=config,
            )
            return LLMResponse(
                content=str(result.content),
                usage=getattr(result, "usage_metadata", {}) or {},
                provider=self.provider_name,
                model=model_name,
                latency_ms=(time.monotonic() - started) * 1000,
            )
        except ValidationError as exc:
            raise LLMValidationError(f"LLM structured output failed validation: {exc}") from exc
        except Exception as exc:
            raise LLMError(f"OpenAI call failed: {exc}") from exc

    def supports_model(self, model: str) -> bool:
        return True

    @staticmethod
    def _to_langchain(messages: list[Message]) -> list[dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in messages]
