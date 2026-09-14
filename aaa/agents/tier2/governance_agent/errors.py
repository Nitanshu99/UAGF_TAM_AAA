"""Errors and article constants for the Phase 5 Governance Agent."""
from __future__ import annotations

from typing import Any

#: Governance articles evidenced by the Phase 5 artefacts: T14 → Art.9 (risk
#: management) / Art.17 (QMS); T15 → Art.12 (record-keeping) / Art.72
#: (post-market monitoring).  When the CGSA self-assessment cannot be
#: retrieved or validated these become INSUFFICIENT_EVIDENCE (→ disclaimer),
#: not a confirmed non-conformity.
GOVERNANCE_INSUFFICIENT_ARTICLES = ["Art.9", "Art.12", "Art.17", "Art.72"]

PROMPT_NAME = "phase5_governance"


class GovernanceAgentError(Exception):
    """Raised when a hard gate blocks Phase 5."""

    def __init__(self, reason: str, details: dict[str, Any] | None = None):
        self.reason = reason
        self.details = details or {}
        super().__init__(f"[GovernanceAgent] {reason}")
