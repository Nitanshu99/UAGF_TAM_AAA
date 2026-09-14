"""IntakeValidator — Stage 0 A/B/C Orchestrator (§6 Stage 0).

Owns the three mandatory pre-audit sub-stages:

  0A · Stage A — Triage: validates the ~20-question form, applies the scope
       gate, previews Art. 43, and writes T01a.
  0B · Stage B — Annex IV dossier: validates the dossier, computes the
       completeness score (gate ≥ 0.80), indexes supporting documents, and
       writes T01b + T01c.
  0C · Stage C — Scoped access (optional): stores only the credential
       reference; when absent, live-system evidence is marked
       ``not_verifiable``.

Returns the fully-populated AuditState ready for Phase 1.
"""
from __future__ import annotations

from aaa.agents.intake_validator.agent import IntakeValidator
from aaa.agents.intake_validator.errors import COMPLETENESS_GATE, IntakeValidatorError

__all__ = ["COMPLETENESS_GATE", "IntakeValidator", "IntakeValidatorError"]
