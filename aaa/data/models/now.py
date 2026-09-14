"""Part 1 of the former ``models`` module (auto-split)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _from_dict(cls: type, d: dict[str, Any]):
    """Build *cls* from *d*, dropping keys that are not declared fields."""
    names = {f.name for f in fields(cls)}
    return cls(**{k: v for k, v in d.items() if k in names})


@dataclass
class EngagementRecord:
    """User-entered data captured at engagement creation time."""

    engagement_id: str
    provider_name: str
    system_name: str
    declared_risk_tier: str
    cgsa_assessment_id: str | None
    status: str
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        """Return the record as a plain JSON-serialisable dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EngagementRecord":
        """Build a record from *d*, ignoring unknown keys."""
        return _from_dict(cls, d)


@dataclass
class IntakeRecord:
    """Stage A / B / C payloads as submitted by the user."""

    engagement_id: str
    stage_a: dict[str, Any]
    stage_b: dict[str, Any]
    stage_c: dict[str, Any] | None
    submitted_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        """Return the record as a plain JSON-serialisable dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "IntakeRecord":
        """Build a record from *d*, ignoring unknown keys."""
        return _from_dict(cls, d)


@dataclass
class UploadedFileMeta:
    """Metadata for one file uploaded by the user (not raw bytes)."""

    engagement_id: str
    filename: str
    role: str          # e.g. "risk_management_file", "model_card", …
    content_type: str
    bytes_size: int
    sha256: str
    uri: str           # EvidenceStore URI
    uploaded_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        """Return the record as a plain JSON-serialisable dict."""
        return asdict(self)
