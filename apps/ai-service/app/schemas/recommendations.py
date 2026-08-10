"""Structured recommendation output."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProductRecommendation(BaseModel):
    product_id: str
    name: str
    reason: str = Field(max_length=500)
    advantages: list[str] = Field(default_factory=list, max_length=6)
    disadvantages: list[str] = Field(default_factory=list, max_length=6)
    score: float = Field(ge=0.0, le=1.0)


class ProductComparison(BaseModel):
    """Comparison of two or more products."""

    products: list[ProductRecommendation] = Field(min_length=2, max_length=3)
    summary: str = Field(max_length=800)


class ProductRanking(BaseModel):
    """Internal ranking of retrieved candidates before the final answer."""

    ranked_product_ids: list[str] = Field(min_length=1, max_length=6)
