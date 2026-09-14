"""Stage 0 gate error and intake constants."""
from __future__ import annotations

from typing import Any

#: Threshold defined in §9.1 and §6.2 constraint 7.
COMPLETENESS_GATE = 0.80

#: Stage B fields whose URIs feed the per-engagement document collection.
_CLIENT_DOC_URI_FIELDS = (
    "risk_management_file_uri",
    "post_market_plan_uri",
    "eu_doc_uri",
    "system_prompt_uri",
    "rag_manifest_uri",
    "guardrail_config_uri",
    "golden_set_uri",
)


class IntakeValidatorError(Exception):
    """Raised when a Stage 0 gate blocks further processing."""

    def __init__(self, stage: str, reason: str, details: dict[str, Any] | None = None):
        self.stage = stage
        self.reason = reason
        self.details = details or {}
        super().__init__(f"[Stage {stage}] {reason}")
