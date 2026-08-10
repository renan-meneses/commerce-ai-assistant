-- Runs on first container boot (docker-entrypoint-initdb.d).
-- The pgvector extension ships with the pgvector/pgvector image; the
-- application migration enables it idempotently as well.
-- Langfuse expects its own database (see docker-compose.yml).

CREATE DATABASE langfuse OWNER commerce;
