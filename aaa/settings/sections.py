"""Field sections composed into :class:`aaa.settings.AAASettings`.

Split by concern to honour the per-file size cap: pipeline/LLM/partner
integrations in one section, backing infrastructure in the other. All
environment variables are documented in ``.env.example``.
"""
from __future__ import annotations

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


class PipelineSection(BaseSettings):
    """Pipeline mode, LLM backends, and partner integrations (S4/S6/S7)."""

    # ── Pipeline mode ──────────────────────────────────────────────────────
    aaa_log_level: str = Field("WARNING", alias="AAA_LOG_LEVEL")

    # ── LLM / LiteLLM ──────────────────────────────────────────────────────
    anthropic_api_key: str = Field("", alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field("", alias="OPENAI_API_KEY")
    openrouter_api_key: str = Field("", alias="OPENROUTER_API_KEY")
    # litellm_model_tier1/2/3 were removed (T-20260806-010): nothing read them,
    # and their claude-* defaults contradicted the live roster. Per-agent model
    # selection lives in aaa/platform/model_registry/, keyed by agent name and
    # switched between the OpenAI and NVIDIA rosters by PROVIDER.

    # Per-model rates for the audit trail's cost column, as JSON, USD per
    # million tokens: {"<model>": {"input": 0.0, "output": 0.0}}. Unset leaves a
    # call LiteLLM cannot price recorded as null / "unpriced" rather than as
    # 0.0000 — zero and unknown are different statements (Q9). No default: the
    # rate is the operator's contract, not something this repo may guess.
    model_prices_usd_per_1m: str = Field("", alias="MODEL_PRICES_USD_PER_1M")

    # ── Embeddings (per purpose: openai | openrouter | local) ──────────────
    # Independent so the confidential client dossier can be embedded on-host
    # while the public regulatory corpus keeps a hosted model's retrieval
    # quality. EMBEDDINGS_LOCAL_MODEL has no default on purpose — choosing
    # "local" must name the model, not inherit someone else's trade-off.
    embeddings_client_docs: str = Field("openai", alias="EMBEDDINGS_CLIENT_DOCS")
    embeddings_regulatory: str = Field("openai", alias="EMBEDDINGS_REGULATORY")
    embeddings_evidence: str = Field("openai", alias="EMBEDDINGS_EVIDENCE")
    embeddings_local_model: str = Field("", alias="EMBEDDINGS_LOCAL_MODEL")

    # ── S4 CGSA integration (§10.2) ────────────────────────────────────────
    s4_cgsa_base_url: str = Field("http://localhost:8001", alias="S4_CGSA_BASE_URL")
    cgsa_schema_version: str = Field("1.0.0", alias="CGSA_SCHEMA_VERSION")
    cgsa_fixture_dir: str = Field("", alias="CGSA_FIXTURE_DIR")

    # ── S6 XAI / S7 Security providers (internal | external, independent) ──
    s6_xai_mode: str = Field("internal", alias="S6_XAI_MODE")
    s6_xai_base_url: str = Field("http://localhost:8006", alias="S6_XAI_BASE_URL")
    s6_xai_bearer_token: str = Field("", alias="S6_XAI_BEARER_TOKEN")
    s7_sec_mode: str = Field("internal", alias="S7_SEC_MODE")
    s7_sec_base_url: str = Field("http://localhost:8007", alias="S7_SEC_BASE_URL")
    s7_sec_bearer_token: str = Field("", alias="S7_SEC_BEARER_TOKEN")


class InfraSection(BaseSettings):
    """Backing infrastructure: stores, queues, vault, observability, servers."""

    # ── Postgres ────────────────────────────────────────────────────────────
    database_url: str = Field(
        "postgresql://aaa:changeme@localhost:5432/aaa", alias="DATABASE_URL"
    )

    # ── MinIO / S3 (EvidenceStore) ──────────────────────────────────────────
    # "memory" keeps artefacts process-local (tests, CI, offline smoke);
    # "minio" persists them so a later process — notably `aaa report` — can
    # still resolve the minio:// URIs the pipeline wrote.
    evidence_backend: str = Field("memory", alias="EVIDENCE_BACKEND")
    minio_endpoint: str = Field("localhost:9000", alias="MINIO_ENDPOINT")
    # The app should hold a service account scoped to its bucket, not the
    # server's root key: MINIO_ACCESS_KEY / MINIO_SECRET_KEY win when set, the
    # root credentials remain the local-dev fallback.
    minio_access_key: str = Field(
        "minioadmin", validation_alias=AliasChoices("MINIO_ACCESS_KEY", "MINIO_ROOT_USER"))
    minio_secret_key: str = Field(
        "", validation_alias=AliasChoices("MINIO_SECRET_KEY", "MINIO_ROOT_PASSWORD"))
    minio_bucket: str = Field("aaa-evidence", alias="MINIO_BUCKET")
    minio_secure: bool = Field(False, alias="MINIO_SECURE")

    # ── Redis / Valkey ──────────────────────────────────────────────────────
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")

    # ── OpenBao (Stage C credential vault) ─────────────────────────────────
    openbao_addr: str = Field("http://localhost:8200", alias="BAO_ADDR")

    # ── Langfuse (observability) ────────────────────────────────────────────
    langfuse_host: str = Field("http://localhost:3003", alias="LANGFUSE_HOST")
    langfuse_public_key: str = Field("", alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field("", alias="LANGFUSE_SECRET_KEY")

    # ── FastAPI platform ────────────────────────────────────────────────────
    platform_host: str = Field("0.0.0.0", alias="PLATFORM_HOST")
    platform_port: int = Field(8000, alias="PLATFORM_PORT")

    # ── Streamlit demo ──────────────────────────────────────────────────────
    streamlit_server_port: int = Field(8501, alias="STREAMLIT_SERVER_PORT")

    # ── Data persistence ────────────────────────────────────────────────────
    aaa_data_dir: str = Field("data", alias="AAA_DATA_DIR")
