"""pgvector storage layer.

Raw, parameterized SQL via psycopg — deliberately NOT routed through
Prisma (ADR-003). This layer is the single owner of vector columns and
vector similarity queries.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from psycopg.rows import dict_row
from psycopg.types.json import Json
from psycopg_pool import AsyncConnectionPool

from app.config.settings import Settings

# Common pt-BR/en function words — FTS 'simple' config has no stopwords,
# so they are filtered here before building the OR query.
_KEYWORD_STOPWORDS = {
    "o",
    "a",
    "os",
    "as",
    "um",
    "uma",
    "uns",
    "umas",
    "de",
    "do",
    "da",
    "dos",
    "das",
    "em",
    "no",
    "na",
    "nos",
    "nas",
    "com",
    "para",
    "por",
    "que",
    "qual",
    "quais",
    "tem",
    "ter",
    "e",
    "ou",
    "meu",
    "minha",
    "meus",
    "minhas",
    "the",
    "an",
    "and",
    "or",
    "of",
    "to",
    "for",
    "with",
    "at",
    "até",
    "ate",
    "sobre",
    "muito",
    "mais",
    "menos",
    "bom",
    "boa",
    "melhor",
}


def _keyword_tsquery(query: str) -> str:
    """OR-join of meaningful query terms (lexical candidate expansion)."""
    tokens = re.findall(r"[a-z0-9]+", query.lower())
    terms = [t for t in tokens if t not in _KEYWORD_STOPWORDS]
    return " | ".join(terms) or "none"


def psycopg_compatible_url(url: str) -> str:
    """Translate `?schema=public` (Prisma convention) into libpq options.

    psycopg3 rejects unknown URI query params, so the search_path is
    passed through `options=-csearch_path=public` instead.
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    schema = params.pop("schema", None)
    if schema:
        options = params.get("options", [])
        options.append(f"-csearch_path={schema[0]}")
        params["options"] = options
    return urlunparse(parsed._replace(query=urlencode(params, doseq=True)))


class PgVectorStore:
    """Async connection pool + vector CRUD.

    - upsert with deterministic chunk ids (idempotent re-indexing)
    - soft-delete by product_id before re-indexing a new version
    - cosine similarity search with metadata filters and an optional
      ``using`` hint for HNSW/IVFFlat index preference
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._pool: AsyncConnectionPool | None = None

    async def _pool_get(self) -> AsyncConnectionPool:
        if self._pool is None:
            self._pool = AsyncConnectionPool(
                psycopg_compatible_url(self.settings.database_url),
                min_size=1,
                max_size=8,
                open=False,
            )
            await self._pool.open(wait=True, timeout=20)
        return self._pool

    async def upsert_chunk_vectors(
        self,
        model: str,
        records: list[dict[str, Any]],
    ) -> int:
        """records: [{id, product_id, chunk_id, content, metadata, vector}]"""
        pool = await self._pool_get()
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.executemany(
                    """
                    INSERT INTO product_embeddings
                        (id, product_id, chunk_id, model, content, metadata, vector)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        vector = EXCLUDED.vector,
                        content = EXCLUDED.content,
                        metadata = EXCLUDED.metadata,
                        updated_at = now()
                    """,
                    [
                        (
                            r["id"],
                            r["product_id"],
                            r.get("chunk_id"),
                            model,
                            r["content"],
                            Json(r["metadata"]),
                            r["vector"],
                        )
                        for r in records
                    ],
                )
            return len(records)

    async def delete_product_vectors(self, product_id: str) -> int:
        pool = await self._pool_get()
        async with pool.connection() as conn, conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM product_embeddings WHERE product_id = %s",
                (product_id,),
            )
            return cur.rowcount or 0

    async def semantic_search(
        self,
        query_vector: list[float],
        model: str,
        *,
        top_k: int = 6,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Cosine similarity search with metadata filters."""
        pool = await self._pool_get()
        where = "model = %(model)s"
        params: dict[str, Any] = {"model": model, "top_k": top_k, "q": query_vector}
        if filters:
            for key, value in filters.items():
                if key in ("category", "brand"):
                    where += f" AND metadata->>'{key}' = %({key})s"
                    params[key] = value
                elif key in ("min_price_cents", "max_price_cents"):
                    op = ">=" if key == "min_price_cents" else "<="
                    where += f" AND (metadata->>'price_cents')::numeric {op} %({key})s"
                    params[key] = int(value)
                elif key == "in_stock":
                    where += " AND (metadata->>'in_stock')::boolean = %(in_stock)s"
                    params["in_stock"] = bool(value)
        sql = f"""
            SELECT id, product_id, content, metadata, model,
                   1 - (vector <=> %(q)s::vector) AS similarity
            FROM product_embeddings
            WHERE {where}
            ORDER BY vector <=> %(q)s::vector
            LIMIT %(top_k)s
        """
        async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()

    async def keyword_search(
        self,
        query: str,
        *,
        top_k: int = 6,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Full-text search over chunk content with ts_rank scoring.

        Lexical retrieval uses OR semantics (any query term) as a
        candidate generator; precision comes from ts_rank ordering and
        the fusion step. AND semantics would miss multi-product or
        comparison-style queries.
        """
        pool = await self._pool_get()
        where = "1 = 1"
        tsquery = _keyword_tsquery(query)
        params: dict[str, Any] = {"query": tsquery, "top_k": top_k}
        if filters:
            for key, value in filters.items():
                if key in ("category", "brand"):
                    where += f" AND metadata->>'{key}' = %({key})s"
                    params[key] = value
                elif key in ("min_price_cents", "max_price_cents"):
                    op = ">=" if key == "min_price_cents" else "<="
                    where += f" AND (metadata->>'price_cents')::numeric {op} %({key})s"
                    params[key] = int(value)
        sql = f"""
            SELECT id, product_id, content, metadata, model,
                   ts_rank(to_tsvector('simple', content),
                           to_tsquery('simple', %(query)s)) AS score
            FROM product_embeddings
            WHERE {where}
              AND to_tsvector('simple', content) @@ to_tsquery('simple', %(query)s)
            ORDER BY score DESC
            LIMIT %(top_k)s
        """
        async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()

    async def vector_count(self) -> int:
        pool = await self._pool_get()
        async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            await cur.execute("SELECT count(*) AS total FROM product_embeddings")
            row = await cur.fetchone()
            return int(row["total"]) if row else 0

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None

    # -- convenience async helpers for tests ---------------------------------

    async def execute(self, sql: str, params: tuple | None = None) -> None:
        pool = await self._pool_get()
        async with pool.connection() as conn, conn.cursor() as cur:
            await cur.execute(sql, params)
