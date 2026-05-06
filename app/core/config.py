"""
app/core/config.py
──────────────────
Centralised settings loaded from environment variables and .env file.
All configuration lives here — never scatter os.environ calls across the codebase.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import AnyHttpUrl, Field, PostgresDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application-wide settings validated and loaded by pydantic-settings.

    Precedence (highest → lowest):
      1. Environment variables
      2. .env file
      3. Default values defined here
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # SUPABASE_URL == supabase_url
        extra="ignore",        # Silently ignore unknown env vars
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_env: str = Field("development", pattern="^(development|staging|production)$")
    app_name: str = "ReRush"
    app_version: str = "0.1.0"
    log_level: str = Field("INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    # ── Server ────────────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = Field(8000, ge=1, le=65535)
    workers: int = Field(1, ge=1)
    reload: bool = True

    # ── Database ──────────────────────────────────────────────────────────────
    supabase_url: AnyHttpUrl
    supabase_anon_key: str
    supabase_service_role_key: str
    database_url: PostgresDsn  # asyncpg connection string

    # ── Embedding ─────────────────────────────────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = Field(384, ge=1)
    embedding_cache_dir: Path = Path(".cache/models")

    # ── TVmaze ────────────────────────────────────────────────────────────────
    tvmaze_base_url: AnyHttpUrl = "https://api.tvmaze.com"  # type: ignore[assignment]
    tvmaze_rate_limit_delay: float = Field(0.2, ge=0.0)

    # ── Search ────────────────────────────────────────────────────────────────
    default_search_limit: int = Field(10, ge=1)
    max_search_limit: int = Field(50, ge=1)
    similarity_threshold: float = Field(0.3, ge=0.0, le=1.0)

    # ── Derived ───────────────────────────────────────────────────────────────
    @model_validator(mode="after")
    def validate_limits(self) -> "Settings":
        if self.default_search_limit > self.max_search_limit:
            raise ValueError(
                f"default_search_limit ({self.default_search_limit}) "
                f"cannot exceed max_search_limit ({self.max_search_limit})"
            )
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def database_url_str(self) -> str:
        """Return the database URL as a plain string for asyncpg."""
        return str(self.database_url)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached Settings instance.
    The cache means we only parse environment variables once per process,
    which is important because sentence-transformers are expensive to load too.
    """
    return Settings()  # type: ignore[call-arg]
