"""Part 1 of the former ``cgsa_ingest`` module (auto-split)."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from aaa.platform.repo_root import REPO_ROOT as _REPO_ROOT

logger = logging.getLogger(__name__)

_VENDORED_SCHEMA = _REPO_ROOT / "schemas" / "cgsa" / "v1.0.0" / "uagf_cgsa_aaa_schema.json"


_LOW_CONFIDENCE_THRESHOLD = 0.6


_REQUIRED_TOP_LEVEL_KEYS = (
    "metadata",
    "overall_scores",
    "domains",
    "eu_ai_act_compliance_matrix",
    "hard_constraint_results",
    "remediation_roadmap",
    "aaa_phase5_handoff",
)


class CGSAIngestError(Exception):
    """Raised when the CGSA payload fails validation or mapping."""

    def __init__(self, reason: str, details: dict[str, Any] | None = None):
        self.reason = reason
        self.details = details or {}
        super().__init__(f"[cgsa_ingest] {reason}")


@dataclass
class IngestResult:
    """Output of ``cgsa_ingest`` — validated payload + state delta."""

    payload: dict[str, Any]
    state_delta: dict[str, Any]
    low_confidence_controls: list[dict[str, Any]] = field(default_factory=list)
    schema_errors: list[str] = field(default_factory=list)
    schema_version: str = "1.0.0"
