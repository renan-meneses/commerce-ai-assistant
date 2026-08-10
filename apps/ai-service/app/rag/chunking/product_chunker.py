"""Deterministic, idempotent chunking.

Chunk ids are derived from (product_id, version, doc_type, chunk_index)
so reprocessing the same document version never creates duplicates.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from app.rag.documents.builder import ProductDoc


@dataclass
class Chunk:
    id: str
    product_id: str
    version: int
    doc_type: str
    chunk_index: int
    content: str
    metadata: dict


class ProductChunker:
    """Splits a product document into semantic chunks.

    Products have short structured documents, so we keep the whole
    document as one chunk and fall back to paragraph-level splitting only
    when the text is long (e.g. rich descriptions). This avoids the
    retrieval quality loss of naive fixed-size splitting.
    """

    def __init__(self, doc_type: str = "description", max_chars: int = 1200):
        self.doc_type = doc_type
        self.max_chars = max_chars

    def chunk(self, doc: ProductDoc) -> list[Chunk]:
        if len(doc.text) <= self.max_chars:
            return [self._make_chunk(doc, 0, doc.text)]

        chunks: list[Chunk] = []
        for para in doc.text.split("\n\n"):
            if not para.strip():
                continue
            chunks.extend(self._split_paragraph(doc, chunks, para))
        return chunks

    def _split_paragraph(self, doc: ProductDoc, chunks: list[Chunk], para: str) -> list[Chunk]:
        """Pack the paragraph into max_chars-sized chunks on word boundaries."""
        pieces: list[str] = []
        current = ""
        for word in para.split():
            if current and len(current) + 1 + len(word) > self.max_chars:
                pieces.append(current)
                current = word
            else:
                current = f"{current} {word}" if current else word
        if current:
            pieces.append(current)
        return [self._make_chunk(doc, len(chunks) + i, piece) for i, piece in enumerate(pieces)]

    def _make_chunk(self, doc: ProductDoc, index: int, content: str) -> Chunk:
        raw_id = f"{doc.product_id}:{doc.version}:{self.doc_type}:{index}"
        return Chunk(
            id=hashlib.sha256(raw_id.encode()).hexdigest(),
            product_id=doc.product_id,
            version=doc.version,
            doc_type=self.doc_type,
            chunk_index=index,
            content=content.strip(),
            metadata={**doc.metadata, "chunk_index": index, "doc_type": self.doc_type},
        )
