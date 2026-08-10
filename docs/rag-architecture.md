# RAG Architecture

## Pipeline

```
product (JSON from API)
  └─ ProductDocumentBuilder  → canonical flat text (name, brand, category, price band, description, specs)
  └─ ProductChunker          → deterministic chunks (sha256 of product_id:version:type:index)
  └─ embeddings              → OpenAI text-embedding-3-small | local bge | hash (dev/CI)
  └─ PgVectorStore           → upsert product_embeddings (ON CONFLICT id)
```

Retrieval at query time:

```
query
  └─ hybrid: semantic_search (cosine, HNSW) + keyword_search (ts_rank, OR terms)
  └─ fusion: Reciprocal Rank Fusion (default) or weighted scores
  └─ SimpleScoreReranker: deterministic score adjustment
  └─ top_k docs → prompt
```

## Storage

`product_embeddings` lives in PostgreSQL via **pgvector 0.8** with an **HNSW index** (`vector_cosine_ops`). The column schema and SQL layer are owned exclusively by the AI service (`app/rag/store/pgvector_store.py`) — Prisma models the relational tables but deliberately not the vector column (ADR-003). psycopg3 is used directly with parameterized SQL; Prisma-style `?schema=public` URLs are translated to libpq `options` for compatibility.

## Idempotency

- Chunk ids are `sha256(product_id:version:doc_type:chunk_index)` — replaying an event overwrites the same rows.
- Before indexing a product, its previous rows are deleted (`delete-before-upsert`) so a stale version never survives.
- `python -m app.indexing.cli --reindex-all` is safe to run repeatedly; the consumer `message.process()` handles redelivery.

## Hybrid retrieval

- **Semantic**: cosine similarity via HNSW, with metadata filters (category, brand, price range, in-stock) pushed into the query.
- **Keyword**: PostgreSQL full-text search over chunk content with `ts_rank` ordering. Terms are OR-joined (any-term matching) after filtering a small pt-BR/en stopword list — AND semantics (`plainto_tsquery`) makes multi-product/comparison queries unanswerable.
- **Fusion**: Reciprocal Rank Fusion (`1/(k+rank)` sums) is robust to score-scale mismatch between cosine and `ts_rank`; `weighted_score_fusion` is available for tuned deployments.

## Chunking

Product documents are short and structured, so the whole document is usually a single chunk (max 1200 chars). Long paragraphs are packed on word boundaries — never naive fixed-size splits — preserving spec lines.

## Embeddings in CI / offline

`EMBEDDINGS_USE_HASH=true` selects a deterministic bag-of-words hashing adapter (feature hashing with signed sums, L2-normalized, `embedding_dimensions`). It only measures lexical overlap, so it is used for smoke tests and CI evaluation, never in production. Langfuse traces record the embedding model name per call.

## Evaluation

`evaluation/datasets/rag_questions.json` contains 10 pt-BR questions aligned with the seeded catalog. `evaluation/reports/` holds generated reports with:

- `recall@k` — expected products found
- category precision — top-1 metadata category
- feature recall — normalized-token overlap for spec features

Run: `make evaluate-rag` (requires indexed data + `EMBEDDINGS_USE_HASH=true` or a key).
