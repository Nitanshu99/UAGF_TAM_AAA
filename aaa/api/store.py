"""
aaa.api.store — In-memory engagement store (replaced by Postgres in production).

Provides a single module-level mutable dict accessed by all API route modules.
Each key is an ``engagement_id`` string.
"""
from __future__ import annotations

from typing import Any

from aaa.platform.evidence import EvidenceStore

# engagement_id → metadata dict
ENGAGEMENTS: dict[str, dict[str, Any]] = {}

# engagement_id → EvidenceStore instance
STORES: dict[str, EvidenceStore] = {}

# engagement_id → raw stage A/B/C intake payload dict
INTAKE_PAYLOADS: dict[str, dict[str, Any]] = {}

# engagement_id → final AuditState dict
FINAL_STATES: dict[str, dict[str, Any]] = {}


def get_store(engagement_id: str) -> EvidenceStore:
    """Return the EvidenceStore for *engagement_id*, creating one if absent."""
    if engagement_id not in STORES:
        STORES[engagement_id] = EvidenceStore()
    return STORES[engagement_id]


__all__ = [
    "ENGAGEMENTS",
    "STORES",
    "INTAKE_PAYLOADS",
    "FINAL_STATES",
    "get_store",
]
