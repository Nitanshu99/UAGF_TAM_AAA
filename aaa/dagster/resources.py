"""
aaa.dagster.resources — Dagster resource definitions.

Resources are shared dependencies injected into Dagster assets/ops:

  - ``evidence_store_resource``  : EvidenceStore (in-memory for now, MinIO in prod)
  - ``settings_resource``        : AAASettings singleton
  - ``llm_audit_resource``       : LLMAuditLogger factory context

Usage in assets::

    @asset(required_resource_keys={"evidence_store", "aaa_settings"})
    def my_asset(context: AssetExecutionContext) -> ...:
        store = context.resources.evidence_store
        cfg = context.resources.aaa_settings
"""
from __future__ import annotations

from dagster import ConfigurableResource, InitResourceContext, resource
from pydantic import Field

from aaa.platform.evidence import EvidenceStore
from aaa.settings import AAASettings, settings as _settings


class EvidenceStoreResource(ConfigurableResource):
    """Dagster resource wrapping EvidenceStore."""

    # In production this would hold MinIO endpoint config.
    backend: str = Field("memory", description="'memory' | 'minio'")

    def create_evidence_store(self) -> EvidenceStore:
        """Return a new EvidenceStore instance."""
        return EvidenceStore()


class AAASettingsResource(ConfigurableResource):
    """Dagster resource exposing AAASettings."""

    def get_settings(self) -> AAASettings:
        return _settings


@resource
def evidence_store_resource(_context: InitResourceContext) -> EvidenceStore:
    """Simple factory resource — returns a fresh EvidenceStore per run."""
    return EvidenceStore()


@resource
def aaa_settings_resource(_context: InitResourceContext) -> AAASettings:
    """Returns the module-level AAASettings singleton."""
    return _settings


__all__ = [
    "EvidenceStoreResource",
    "AAASettingsResource",
    "evidence_store_resource",
    "aaa_settings_resource",
]
