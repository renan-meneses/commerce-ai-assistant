# Database Design

## ER model (Prisma — `apps/api/prisma/schema.prisma`)

```
users ──< carts ──< cart_items >── products <── categories
  │                                   │
  └──< orders ──< order_items >───────┘

products <── product_documents <── product_chunks
products <── product_embeddings     (vector column, AI service only)
```

| Table | Notes |
|---|---|
| `users` | email/passwordHash/name; email unique |
| `categories` | name/slug unique |
| `products` | sku unique, category FK, `price_cents` integer, `specifications` JSONB, optimistic `version` int |
| `inventory` | productId FK unique, quantity/reserved; available = quantity − reserved |
| `carts` / `cart_items` | unique(userId, productId) |
| `orders` / `order_items` | order `number` unique, status enum (PENDING/PAID/SHIPPED/DELIVERED/CANCELLED), total_cents |
| `product_documents` | canonical document text per product version |
| `product_chunks` | chunk text + ordering for the AI service |
| `product_embeddings` | **vector column** — see below |

## pgvector

`product_embeddings` is created by the migration `20260810175929_init` (appended pgvector SQL):

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE product_embeddings (
    id TEXT PRIMARY KEY,            -- sha256 chunk id (idempotent upserts)
    product_id UUID NOT NULL,
    chunk_id TEXT,
    model TEXT NOT NULL,            -- embedding model used
    content TEXT NOT NULL,
    metadata JSONB NOT NULL,        -- category, brand, price_cents, in_stock, sku…
    vector vector(1536) NOT NULL,
    created_at/updated_at
);
CREATE INDEX product_embeddings_hnsw ON product_embeddings
    USING hnsw (vector vector_cosine_ops);
CREATE INDEX product_embeddings_product ON product_embeddings(product_id);
```

Design choices:

- **Deterministic primary key** (chunk id) → `ON CONFLICT (id) DO UPDATE` gives replay-safe indexing.
- **Integer cents** for money (`price_cents`) — no floating point.
- **JSONB metadata + generated-filter predicates** — filters like `metadata->>'category'` keep vector search filterable without extra joins.
- **Ownership split**: Prisma owns relational tables; the AI service owns the vector column via raw psycopg SQL (ADR-003). No cross-service writes: the AI service only reads products via HTTP and writes only `product_embeddings`.

## Migrations

```bash
cd apps/api
yarn prisma migrate dev --name <change>   # development
yarn prisma migrate deploy                # CI / production
```

The initial migration embeds the pgvector extension + index (re-run in CI via `migrate deploy` on the pgvector image).

## Seeding

`prisma/seed.ts` creates categories (Notebooks, Smartphones, Monitores, Acessórios), 59 products with realistic pt-BR specs/descriptions and a demo user `demo@commerce.ai` / `demo1234`. The RAG evaluation dataset is aligned with this catalog.

## Indexing lifecycle

1. Product saved → API publishes `product.created/updated` → worker reindexes that product.
2. `--reindex-all` rebuilds the whole vector store (delete-before-upsert per product).
