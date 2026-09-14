"""Error type and prompt name for the Phase 2 Data Auditor."""
from __future__ import annotations

from typing import Any

_PROMPT_NAME = "phase2_data"


class DataAuditorError(Exception):
    """Raised when a hard gate blocks Phase 2."""

    def __init__(self, reason: str, details: dict[str, Any] | None = None):
        self.reason = reason
        self.details = details or {}
        super().__init__(f"[DataAuditor] {reason}")
