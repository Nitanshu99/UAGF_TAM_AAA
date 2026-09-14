"""One graded article status, with the reasons a reader needs."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Grade:
    """A T15 article status, the rationale for it, and the observations it adds."""

    status: str
    rationale: str
    observations: list[str] = field(default_factory=list)


__all__ = ["Grade"]
