"""Error types raised by the Phase 3 ModelValidator."""
from __future__ import annotations

from typing import Any


class ModelValidatorError(Exception):
    """Raised when a hard gate blocks Phase 3.

    :param reason: Human-readable description of the gate that failed.
    :param details: Optional structured context for the failure.
    """

    def __init__(self, reason: str, details: dict[str, Any] | None = None):
        self.reason = reason
        self.details = details or {}
        super().__init__(f"[ModelValidator] {reason}")
