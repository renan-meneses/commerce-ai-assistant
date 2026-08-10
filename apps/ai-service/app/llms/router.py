"""Task-aware model router with fallback support."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.config.settings import Settings
from app.llms.base import LLMError, LLMProvider
from app.llms.openai_adapter import OpenAIAdapter

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TaskTier:
    """A task classification tier: cheap/latency-sensitive or strong/reasoning."""

    name: str
    latency_sensitive: bool = False


TASK_CHEAP = TaskTier("cheap", latency_sensitive=True)
TASK_STRONG = TaskTier("strong")


@dataclass
class ModelRouter:
    """Maps tasks to model tiers.

    Strategy:
    - intent classification and requirement extraction -> cheap, low-latency model
    - recommendation and comparison -> stronger reasoning model
    - fallback: if the preferred provider/model fails, degrade to the
      default chat model before surfacing an error.
    """

    settings: Settings
    providers: list[LLMProvider] = field(default_factory=list)
    default_provider: LLMProvider | None = None

    def __post_init__(self) -> None:
        if not self.providers:
            self.providers = [OpenAIAdapter(self.settings)]
        self.default_provider = self.providers[0]

    def tier_for(self, task: str) -> TaskTier:
        return TASK_STRONG if task in self.settings.router_strong_task else TASK_CHEAP

    def model_for(self, task: str) -> str | None:
        tier = self.tier_for(task)
        if tier is TASK_STRONG:
            return self.settings.openai_model_strong
        return self.settings.openai_model_chat

    async def generate(
        self,
        task: str,
        messages: list,
        *,
        response_model=None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        callbacks: list | None = None,
    ):
        """Generate with the tier's model, falling back across providers/models."""
        model = self.model_for(task)
        errors: list[str] = []
        for provider in self.providers:
            try:
                return await provider.generate(
                    messages,
                    model=model,
                    response_model=response_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    callbacks=callbacks,
                )
            except LLMError as exc:
                errors.append(f"{provider.provider_name}: {exc}")
                logger.warning(
                    "provider %s failed for task %s: %s", provider.provider_name, task, exc
                )
                if not self.settings.llm_model_fallback_enabled:
                    break
        raise LLMError(f"all LLM providers failed for task {task}: {'; '.join(errors)}")
