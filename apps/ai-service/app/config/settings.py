"""Application configuration for the AI service."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../../.env.example", ".env"),
        extra="ignore",
        case_sensitive=False,
    )

    # --- service ---
    app_name: str = "commerce-ai-service"
    environment: str = "development"

    # --- database ---
    database_url: str = "postgresql://commerce:commerce_dev_password@localhost:5432/commerce"
    # AI service uses a separate read user concept in production; keep single URL for dev.

    # --- redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- rabbitmq (indexing events) ---
    rabbitmq_url: str = "amqp://commerce:commerce_dev_password@localhost:5672"
    rabbitmq_indexing_queue: str = "commerce.indexing.product"

    # --- commerce API (tool backend) ---
    api_url: str = "http://localhost:3000"

    # --- auth propagation ---
    jwt_secret: str = "dev-secret-change-me"

    # --- LLM providers ---
    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_model_chat: str = "gpt-4o-mini"
    openai_model_strong: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    llm_model_fallback_enabled: bool = True

    # --- embeddings ---
    embeddings_use_local: bool = False
    embeddings_use_hash: bool = False  # deterministic BOW hashing: offline dev/CI only
    embeddings_local_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dimensions: int = 1536

    # --- model routing thresholds ---
    router_strong_task: set[str] = Field(default_factory=lambda: {"COMPARE", "RECOMMENDATION"})

    # --- caching TTLs (seconds) ---
    cache_product_ttl: int = 3600  # product catalog data: long TTL
    cache_search_ttl: int = 300  # semantic search results: medium TTL
    cache_price_ttl: int = 30  # prices: short TTL
    cache_inventory_ttl: int = 0  # inventory: no cache (live truth)

    # --- observability ---
    langfuse_enabled: bool = False
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://localhost:3002"
    tracing_enabled: bool = False
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"

    # --- agent limits ---
    agent_max_iterations: int = 5
    agent_max_tokens: int = 1500
    retrieval_top_k: int = 6
    retrieval_candidates: int = 12


@lru_cache
def get_settings() -> Settings:
    return Settings()
