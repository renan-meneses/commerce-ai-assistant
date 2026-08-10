"""Product -> document building.

Transforms a product (name, description, specs, brand, price band) into
a normalized text document plus metadata for hybrid retrieval.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ProductDoc:
    product_id: str
    version: int
    text: str
    metadata: dict = field(default_factory=dict)


class ProductDocumentBuilder:
    """Builds the canonical searchable document for a product.

    The document text is deliberately flat and descriptive so that both
    semantic (embedding) and lexical (FTS/trigram) retrieval work well.
    """

    def _category_name(self, product: dict) -> str:
        category = product.get("category_name") or product.get("category") or ""
        if isinstance(category, dict):
            category = category.get("name") or category.get("slug") or ""
        return category

    def build(self, product: dict) -> ProductDoc:
        specs = product.get("specifications") or {}
        spec_lines = [self._normalize_key(key) + ": " + str(value) for key, value in specs.items()]

        category_name = self._category_name(product)
        price_band = self._price_band(product.get("price_cents") or product.get("priceCents") or 0)

        text = "\n".join(
            [
                f"Product: {product.get('name', '')}",
                f"Brand: {product.get('brand', '')}",
                f"Category: {self._normalize_key(category_name)}",
                f"Price: {price_band}",
                f"Description: {product.get('description', '')}",
                "Specifications:",
                *[f"- {line}" for line in spec_lines],
            ]
        )

        metadata = {
            "product_id": str(product.get("id") or product.get("product_id") or ""),
            "category": category_name,
            "brand": product.get("brand"),
            "price_cents": product.get("price_cents") or product.get("priceCents"),
            "in_stock": bool(product.get("in_stock", True)),
            "sku": product.get("sku"),
        }
        return ProductDoc(
            product_id=str(metadata["product_id"] or ""),
            version=int(product.get("version") or 1),
            text=self.normalize(text),
            metadata=metadata,
        )

    @staticmethod
    def normalize(text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _normalize_key(key: str) -> str:
        return re.sub(r"(?<!^)(?=[A-Z])", " ", key).replace("_", " ").replace("-", " ").title()

    @staticmethod
    def _price_band(price_cents: int) -> str:
        band = price_cents // 100000  # per R$1.000
        if band <= 0:
            return "under R$1.000"
        if band <= 3:
            return f"around R${band * 1000 - 500} to R${band * 1000}"
        if band <= 8:
            return f"from R${band * 1000} to R${band * 1000 + 1000}"
        return f"above R${band * 1000}"
