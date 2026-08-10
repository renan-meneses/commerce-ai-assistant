"""Unit tests for product -> document building."""

from app.rag.documents.builder import ProductDocumentBuilder


def test_category_dict_is_unwrapped():
    builder = ProductDocumentBuilder()
    doc = builder.build(
        {
            "id": "p1",
            "name": "ASUS Vivobook 16X",
            "brand": "ASUS",
            "category": {"name": "Notebooks", "slug": "notebooks"},
            "description": "Ideal para desenvolvimento de software.",
            "price_cents": 489900,
            "specifications": {"ram": "16 GB DDR4", "storage": "512 GB NVMe SSD"},
        }
    )
    assert "Category: Notebooks" in doc.text
    assert doc.metadata["category"] == "Notebooks"
    assert doc.metadata["product_id"] == "p1"
    assert "Ram: 16 GB DDR4" in doc.text
    assert "Storage: 512 GB NVMe SSD" in doc.text


def test_category_string_is_kept():
    builder = ProductDocumentBuilder()
    doc = builder.build(
        {"id": "p2", "name": "X", "brand": "Y", "category": "Smartphones", "price_cents": 1000}
    )
    assert doc.metadata["category"] == "Smartphones"


def test_price_bands():
    builder = ProductDocumentBuilder()
    cheap = builder.build({"id": "p", "name": "X", "brand": "Y", "price_cents": 89900})
    mid = builder.build({"id": "p", "name": "X", "brand": "Y", "price_cents": 489900})
    high = builder.build({"id": "p", "name": "X", "brand": "Y", "price_cents": 1199900})
    assert "under R$1.000" in cheap.text
    assert "R$4000 to R$5000" in mid.text
    assert "above R$11000" in high.text


def test_normalize_collapses_whitespace():
    builder = ProductDocumentBuilder()
    doc = builder.build(
        {
            "id": "p",
            "name": "X",
            "brand": "Y",
            "description": "line one\n\n  line two",
            "price_cents": 100,
        }
    )
    assert "\n" not in doc.text
