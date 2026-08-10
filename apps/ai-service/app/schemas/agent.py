"""Structured outputs used across the agent.

Every LLM-generated value is validated through these Pydantic models
before the agent acts on it.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class IntentClassification(BaseModel):
    """Routing decision for the user request."""

    intent: Literal[
        "PRODUCT_SEARCH",
        "PRODUCT_RECOMMENDATION",
        "COMPARE_PRODUCTS",
        "PRODUCT_PRICE",
        "INVENTORY",
        "ORDER_STATUS",
        "SHIPPING",
        "GENERAL_KNOWLEDGE",
        "REFUSED",
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(max_length=300)
    requires_user_context: bool = False


class ExtractedRequirements(BaseModel):
    """Requirements parsed from the user's natural language request."""

    category: str | None = None
    brand: str | None = None
    min_price_cents: int | None = Field(default=None, ge=0)
    max_price_cents: int | None = Field(default=None, ge=0)
    features: list[str] = Field(default_factory=list, max_length=10)
    quantity: int | None = Field(default=None, ge=1)
    order_number: str | None = None
    product_names: list[str] = Field(default_factory=list, max_length=5)
