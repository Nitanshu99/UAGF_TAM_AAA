"""Part 2 of the former ``models`` module (auto-split)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from aaa.data.models.now import (  # noqa: F401
    EngagementRecord,
    IntakeRecord,
    UploadedFileMeta,
    _from_dict,
    _now,
)


@dataclass
class AuditResult:
    """Final audit outcome written after the pipeline completes."""

    engagement_id: str
    final_verdict: str
    intake_completeness_score: float | None
    completeness_score: float | None
    regulatory_coverage_pct: float | None
    material_findings_count: int | None
    possibly_material_findings_count: int | None
    auditor_opinion: str | None
    art43_procedure: str | None
    completed_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        """Return the record as a plain JSON-serialisable dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AuditResult":
        """Build a record from *d*, ignoring unknown keys."""
        return _from_dict(cls, d)


@dataclass
class FindingsRecord:
    """Blocking and positive findings together with the remediation roadmap."""

    engagement_id: str
    blocking_findings: list[dict[str, Any]]
    positive_findings: list[dict[str, Any]]
    remediation_roadmap: list[dict[str, Any]]
    recorded_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        """Return the record as a plain JSON-serialisable dict."""
        return asdict(self)


__all__ = [
    "EngagementRecord",
    "IntakeRecord",
    "UploadedFileMeta",
    "AuditResult",
    "FindingsRecord",
]
