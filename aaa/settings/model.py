"""The composed settings model and its module-level singleton (§14.3).

Values are read from environment variables (or a ``.env`` file in the repo
root when ``python-dotenv`` is installed). No secret values are logged or
printed — only non-sensitive metadata fields are exposed via ``safe_repr``.
"""
from __future__ import annotations

from pydantic_settings import SettingsConfigDict

from aaa.platform.env_bootstrap import under_pytest
from aaa.settings.sections import InfraSection, PipelineSection


class AAASettings(PipelineSection, InfraSection):
    """Pydantic-settings model for the AAA pipeline."""

    # No `.env` under pytest, for the same reason `load_repo_dotenv` skips it:
    # a developer's file must not bleed into the tests. A checkout set up by
    # `bootstrap.py` carries EMBEDDINGS_*=openrouter, and every test that
    # asserts the shipped defaults failed there while passing in CI.
    model_config = SettingsConfigDict(
        env_file=None if under_pytest() else ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def safe_repr(self) -> dict:
        """Return non-sensitive settings for logging / health-check endpoints.

        :returns: Metadata fields only — never credentials or tokens.
        :rtype: dict
        """
        return {
            "aaa_log_level": self.aaa_log_level,
            "aaa_data_dir": self.aaa_data_dir,
            "s4_cgsa_base_url": self.s4_cgsa_base_url,
            "cgsa_schema_version": self.cgsa_schema_version,
            "s6_xai_mode": self.s6_xai_mode,
            "s6_xai_base_url": self.s6_xai_base_url,
            "s7_sec_mode": self.s7_sec_mode,
            "s7_sec_base_url": self.s7_sec_base_url,
            "minio_endpoint": self.minio_endpoint,
            "minio_bucket": self.minio_bucket,
            "langfuse_host": self.langfuse_host,
            "platform_port": self.platform_port,
        }


# Module-level singleton — import this object, do not re-instantiate.
# pyright can't see that BaseSettings populates aliased fields from the
# environment, so the zero-arg constructor is a false positive here.
settings = AAASettings()  # pyright: ignore[reportCallIssue]
