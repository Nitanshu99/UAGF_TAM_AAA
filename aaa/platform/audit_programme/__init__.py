"""audit_programme — procedures, their outcomes, and the scope limitations they imply.

Whether a Tier-3 spawn's articles lose their evidence used to depend on the spawn's
self-reported confidence, which no rule tied to what had run — and two of the three
spawns never reached the confidence gate at all. The decision now rests on recorded
procedure outcomes read against a fixed programme.
"""
from __future__ import annotations

from aaa.platform.audit_programme.apply import apply_audit_programme
from aaa.platform.audit_programme.procedures import (
    NOT_PERFORMED,
    PERFORMED,
    PROGRAMME,
    Procedure,
    outcome,
)

__all__ = ["NOT_PERFORMED", "PERFORMED", "PROGRAMME", "Procedure", "apply_audit_programme",
           "outcome"]
