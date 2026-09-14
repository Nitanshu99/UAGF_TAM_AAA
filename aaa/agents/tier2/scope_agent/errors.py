"""Error type, prompt name, and Art. 5 markers for the Phase 1 agent."""
from __future__ import annotations

from typing import Any

_PROMPT_NAME = "phase1_scope"

#: Art. 5 prohibited practice markers (simplified; full list in Annex to Act).
_ART5_MARKERS: list[str] = [
    "subliminal manipulation",
    "exploit vulnerability",
    "social scoring",
    "real-time remote biometric identification in public spaces",
    "real-time biometric identification in public space",
    "prohibited practice",
    "emotion inference in workplace",
    "untargeted facial image scraping",
    "predictive policing based solely on profiling",
]


class ScopeAgentError(Exception):
    """Raised when a hard gate (Art. 5 prohibition or schema failure) blocks Phase 1."""

    def __init__(self, reason: str, details: dict[str, Any] | None = None):
        self.reason = reason
        self.details = details or {}
        super().__init__(f"[ScopeAgent] {reason}")
