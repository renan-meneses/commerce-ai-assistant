"""Unit tests for the model router."""

import pytest

from app.config.settings import Settings
from app.llms.base import LLMError, LLMResponse, Message
from app.llms.router import TASK_CHEAP, TASK_STRONG, ModelRouter


class FailingProvider:
    provider_name = "failing"

    async def generate(self, messages, **kwargs):
        raise LLMError("boom")


class OkProvider:
    provider_name = "ok"

    async def generate(self, messages, **kwargs):
        return LLMResponse(content="{}", provider=self.provider_name)


def _settings(**overrides) -> Settings:
    data = {"openai_api_key": "test-key", "llm_model_fallback_enabled": True}
    data.update(overrides)
    return Settings(**data)


def test_tier_mapping():
    router = ModelRouter(settings=_settings(), providers=[])
    assert router.tier_for("intent") is TASK_CHEAP
    assert router.tier_for("extract") is TASK_CHEAP
    assert router.tier_for("RECOMMENDATION") is TASK_STRONG
    assert router.tier_for("COMPARE") is TASK_STRONG


def test_model_selection():
    settings = _settings(openai_model_chat="cheap-model", openai_model_strong="strong-model")
    router = ModelRouter(settings=settings, providers=[])
    assert router.model_for("intent") == "cheap-model"
    assert router.model_for("RECOMMENDATION") == "strong-model"


@pytest.mark.asyncio
async def test_fallback_across_providers():
    router = ModelRouter(settings=_settings(), providers=[FailingProvider(), OkProvider()])
    response = await router.generate("intent", [Message(role="user", content="hi")])
    assert response.provider == "ok"


@pytest.mark.asyncio
async def test_fallback_disabled_raises():
    router = ModelRouter(
        settings=_settings(llm_model_fallback_enabled=False),
        providers=[FailingProvider()],
    )
    with pytest.raises(LLMError):
        await router.generate("intent", [Message(role="user", content="hi")])
