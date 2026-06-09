"""
aaa.settings — Centralised configuration via pydantic-settings (§14.3).

All environment variables are documented in ``.env.example``.
Import the singleton ``settings`` object wherever you need a config value::

    from aaa.settings import settings

    if settings.aaa_offline_mode:
        ...

Values are read from environment variables (or a ``.env`` file in the repo
root when ``python-dotenv`` is installed).  No secret values are logged or
printed — only non-sensitive metadata fields are exposed.
"""
from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AAASettings(BaseSettings):
    """Pydantic-settings model for the AAA pipeline."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Pipeline mode ──────────────────────────────────────────────────────
    aaa_offline_mode: bool = Field(False, alias="AAA_OFFLINE_MODE")
    aaa_log_level: str = Field("WARNING", alias="AAA_LOG_LEVEL")

    # ── LLM / LiteLLM ──────────────────────────────────────────────────────
    anthropic_api_key: str = Field("", alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field("", alias="OPENAI_API_KEY")
    litellm_model_tier1: str = Field("claude-opus-4-5", alias="LITELLM_MODEL_TIER1")
    litellm_model_tier2: str = Field("claude-sonnet-4-5", alias="LITELLM_MODEL_TIER2")
    litellm_model_tier3: str = Field("claude-sonnet-4-5", alias="LITELLM_MODEL_TIER3")

    # ── S4 CGSA integration (§10.2) ────────────────────────────────────────
    s4_cgsa_base_url: str = Field("http://localhost:8001", alias="S4_CGSA_BASE_URL")
    cgsa_schema_version: str = Field("1.0.0", alias="CGSA_SCHEMA_VERSION")
    cgsa_fixture_dir: str = Field("", alias="CGSA_FIXTURE_DIR")

    # ── Postgres ────────────────────────────────────────────────────────────
    database_url: str = Field(
        "postgresql://aaa:changeme@localhost:5432/aaa", alias="DATABASE_URL"
    )

    # ── MinIO / S3 (EvidenceStore) ──────────────────────────────────────────
    minio_endpoint: str = Field("localhost:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field("minioadmin", alias="MINIO_ROOT_USER")
    minio_secret_key: str = Field("", alias="MINIO_ROOT_PASSWORD")
    minio_bucket: str = Field("aaa-evidence", alias="MINIO_BUCKET")
    minio_secure: bool = Field(False, alias="MINIO_SECURE")

    # ── Redis / Valkey ──────────────────────────────────────────────────────
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")

    # ── OpenBao (Stage C credential vault) ─────────────────────────────────
    openbao_addr: str = Field("http://localhost:8200", alias="BAO_ADDR")

    # ── Langfuse (observability) ────────────────────────────────────────────
    langfuse_host: str = Field("http://localhost:3003", alias="LANGFUSE_HOST")
    langfuse_public_key: str = Field("", alias="LANGFUSE_PUBLIC_KEY")

    # ── FastAPI platform ────────────────────────────────────────────────────
    platform_host: str = Field("0.0.0.0", alias="PLATFORM_HOST")
    platform_port: int = Field(8000, alias="PLATFORM_PORT")

    # ── Streamlit demo ──────────────────────────────────────────────────────
    streamlit_server_port: int = Field(8501, alias="STREAMLIT_SERVER_PORT")

    # ── Data persistence ────────────────────────────────────────────────────
    aaa_data_dir: str = Field("data", alias="AAA_DATA_DIR")

    def is_offline(self) -> bool:
        """Return True when running in fully offline/demo mode."""
        return self.aaa_offline_mode or bool(self.cgsa_fixture_dir)

    def safe_repr(self) -> dict:
        """Return non-sensitive settings for logging / health-check endpoints."""
        return {
            "aaa_offline_mode": self.aaa_offline_mode,
            "aaa_log_level": self.aaa_log_level,
            "aaa_data_dir": self.aaa_data_dir,
            "s4_cgsa_base_url": self.s4_cgsa_base_url,
            "cgsa_schema_version": self.cgsa_schema_version,
            "minio_endpoint": self.minio_endpoint,
            "minio_bucket": self.minio_bucket,
            "langfuse_host": self.langfuse_host,
            "platform_port": self.platform_port,
            "litellm_model_tier1": self.litellm_model_tier1,
            "litellm_model_tier2": self.litellm_model_tier2,
            "litellm_model_tier3": self.litellm_model_tier3,
        }


# Module-level singleton — import this object, do not re-instantiate.
settings = AAASettings()
