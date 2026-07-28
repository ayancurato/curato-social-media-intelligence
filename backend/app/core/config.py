"""
Curato AI — Application Configuration

Centralized settings management using Pydantic BaseSettings.
All configuration is loaded from environment variables.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────
    app_name: str = "Curato AI"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    log_level: str = "INFO"

    # ── Database ─────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://curato:curato_secret@localhost:5432/curato_ai",
        description="Async database connection string (asyncpg driver)",
    )
    database_url_sync: str = Field(
        default="postgresql://curato:curato_secret@localhost:5432/curato_ai",
        description="Sync database connection string (for Alembic migrations)",
    )
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_pre_ping: bool = True

    # ── Redis ────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Celery ───────────────────────────────────────────────────────────
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # ── CORS ─────────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # ── LLM Defaults ─────────────────────────────────────────────────────
    openai_api_key: str = ""
    openai_base_url: str | None = None
    default_llm_provider: str = "openai"
    default_llm_model: str = "gpt-4.1"
    default_llm_temperature: float = 0.7
    default_llm_max_tokens: int = 4096

    # ── Agent Configuration ──────────────────────────────────────────────
    agent_max_retries: int = 3
    agent_retry_delay_seconds: int = 2

    # ── Google Integrations (not implemented yet) ────────────────────────
    google_service_account_key_path: str = ""
    google_docs_template_id: str = ""
    google_sheets_id: str = ""


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — loaded once, reused everywhere."""
    return Settings()
