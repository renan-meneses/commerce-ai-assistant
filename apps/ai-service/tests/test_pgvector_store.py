"""Unit tests for pgvector store helpers."""

from app.rag.store.pgvector_store import _keyword_tsquery, psycopg_compatible_url


def test_schema_param_becomes_libpq_options():
    url = psycopg_compatible_url("postgresql://u:p@localhost:5432/db?schema=public")
    assert "schema=" not in url
    assert "-csearch_path" in url


def test_url_without_schema_unchanged():
    url = psycopg_compatible_url("postgresql://u:p@localhost:5432/db")
    assert url == "postgresql://u:p@localhost:5432/db"


def test_keyword_tsquery_drops_stopwords():
    query = _keyword_tsquery("qual notebook com 16 gb de ram para rodar docker?")
    terms = set(query.split(" | "))
    assert "qual" not in terms
    assert "com" not in terms
    assert "de" not in terms
    assert "para" not in terms
    assert {"notebook", "16", "gb", "ram", "rodar", "docker"} <= terms


def test_keyword_tsquery_uses_or_semantics():
    query = _keyword_tsquery("asus vivobook lenovo ideapad")
    assert "|" in query
