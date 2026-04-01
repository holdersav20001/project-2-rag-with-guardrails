"""Application settings — loaded once, cached forever. API_KEY must be non-empty."""
from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Security — no default; startup fails if unset or empty
    api_key: str

    # LLM — OpenRouter (OpenAI-compatible)
    openrouter_api_key: str
    openrouter_model: str = "anthropic/claude-3.5-sonnet"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Database
    database_url: str

    # Embeddings & models
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embed_dim: int = 384
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    nli_model: str = "cross-encoder/nli-deberta-v3-small"
    hf_cache_dir: str = "/app/.cache/huggingface"

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 50

    # Guardrails
    topic_similarity_threshold: float = 0.25
    max_upload_size_mb: int = 50

    # Rate limiting
    query_rate_limit: str = "30/minute"
    upload_rate_limit: str = "10/minute"

    # Observability
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    log_level: str = "INFO"

    @field_validator("api_key")
    @classmethod
    def api_key_must_not_be_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError(
                "API_KEY must be set to a non-empty value. "
                "Set it in your .env file or environment."
            )
        # Store stripped so comparison in auth layer is exact (no .strip() needed there)
        return stripped

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
