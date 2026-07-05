from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Inbound auth ─────────────────────────────────────────
    ktrt_api_key: str = Field(default="", alias="KTRT_API_KEY")

    # ── Provider keys ────────────────────────────────────────
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    azure_openai_api_key: str = Field(default="", alias="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: str = Field(default="", alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment: str = Field(default="gpt-5.4-pro", alias="AZURE_OPENAI_DEPLOYMENT")
    azure_openai_api_version: str = Field(
        default="2025-01-01-preview", alias="AZURE_OPENAI_API_VERSION"
    )
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    mistral_api_key: str = Field(default="", alias="MISTRAL_API_KEY")

    # ── Research ─────────────────────────────────────────────
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")
    exa_api_key: str = Field(default="", alias="EXA_API_KEY")
    searxng_url: str = Field(default="", alias="SEARXNG_URL")

    # ── Storage ──────────────────────────────────────────────
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    database_url: str = Field(
        default="",
        alias="DATABASE_URL",
    )

    # ── Workflow defaults ────────────────────────────────────
    max_debate_rounds: int = Field(default=3, alias="MAX_DEBATE_ROUNDS")
    max_debug_rounds: int = Field(default=3, alias="MAX_DEBUG_ROUNDS")
    default_mode: str = Field(default="research", alias="DEFAULT_MODE")

    # ── CORS ─────────────────────────────────────────────────
    # Comma-separated list of allowed origins, e.g. "https://app.example.com,https://gpt.example.com"
    # Defaults to "*" (all origins). Restrict this in production.
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")

    # ── Observability ────────────────────────────────────────
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    # ── Timeouts (seconds) ──────────────────────────────────
    search_timeout: int = 15
    total_workflow_timeout: int = 180


settings = Settings()
