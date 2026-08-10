"""Scripted LLM provider for evaluation and behavioral tests.

Returns canned, schema-valid responses per task. This lets the agent
graph run end-to-end without network calls — the evaluation measures
routing, tools and security behavior, not model quality.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from app.llms.base import LLMResponse, Message


class ScriptedLLMProvider:
    """Responds deterministically by task name.

    Configure ``responses[task]`` as a callable(messages) -> dict (raw
    data to be validated as JSON) or a static dict/string.
    """

    provider_name = "scripted"

    def __init__(self, responses: dict[str, Any] | None = None):
        self.responses = responses or {}

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
        task = self._detect_task(messages)
        factory = self.responses.get(task)
        if factory is None:
            raise RuntimeError(f"no scripted response for task {task}")
        data = factory(messages) if callable(factory) else factory
        if response_model is not None:
            payload = data if isinstance(data, BaseModel) else response_model.model_validate(data)
            content = payload.model_dump_json()
        else:
            content = data if isinstance(data, str) else json.dumps(data)
        return LLMResponse(
            content=content,
            provider=self.provider_name,
            model="scripted",
            latency_ms=0.0,
        )

    def supports_model(self, model: str) -> bool:
        return True

    @staticmethod
    def _detect_task(messages: list[Message]) -> str:
        for m in messages:
            if m.role == "system":
                content = m.content.lower()
                if "classify the user request" in content:
                    return "intent"
                if "extract the product requirements" in content:
                    return "extract"
                if "rank candidates by relevance" in content:
                    return "rank"
                if "shopping assistant" in content:
                    return "response"
        return "response"
