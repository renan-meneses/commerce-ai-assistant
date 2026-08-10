"""Unit tests for the deterministic product chunker."""

from app.rag.chunking.product_chunker import ProductChunker
from app.rag.documents.builder import ProductDoc


def _doc(text: str, product_id: str = "p1", version: int = 3) -> ProductDoc:
    return ProductDoc(
        product_id=product_id,
        version=version,
        text=text,
        metadata={"category": "Notebooks", "price_cents": 489900},
    )


def test_short_document_is_single_chunk():
    chunks = ProductChunker().chunk(_doc("Product: X\nBrand: Y"))
    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].doc_type == "description"


def test_long_document_is_split_by_paragraphs():
    text = "\n\n".join(f"Paragraph {i} " + "word " * 400 for i in range(4))
    chunks = ProductChunker(max_chars=1200).chunk(_doc(text))
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.content.strip()
        assert len(chunk.content) <= 1200


def test_chunk_ids_are_deterministic():
    doc = _doc("Product: Deterministic content\nBrand: X")
    first = ProductChunker().chunk(doc)
    second = ProductChunker().chunk(doc)
    assert [c.id for c in first] == [c.id for c in second]


def test_chunk_id_changes_with_version():
    doc_v2 = _doc("Product: Deterministic content\nBrand: X", version=2)
    doc_v3 = _doc("Product: Deterministic content\nBrand: X", version=3)
    assert ProductChunker().chunk(doc_v2)[0].id != ProductChunker().chunk(doc_v3)[0].id


def test_chunk_metadata_carries_doc_metadata():
    doc = _doc("Product: X")
    chunk = ProductChunker().chunk(doc)[0]
    assert chunk.metadata["category"] == "Notebooks"
    assert chunk.metadata["chunk_index"] == 0
    assert chunk.metadata["doc_type"] == "description"
