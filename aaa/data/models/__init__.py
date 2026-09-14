"""aaa.data.models — Dataclass models for the data persistence layer.

These are plain Python dataclasses (not Pydantic) — they are used only
for structured serialisation to / from JSON on disk.  No ORM, no DB.

Classes
-------
EngagementRecord  — created when the user creates an engagement.
IntakeRecord      — created when the user submits Stage A/B/C payloads.
UploadedFileMeta  — one entry per file the user uploads.
AuditResult       — created when the pipeline completes (final verdict + KPIs).
FindingsRecord    — blocking/positive findings + remediation roadmap."""
from aaa.data.models.auditresult import AuditResult, FindingsRecord  # noqa: F401
from aaa.data.models.now import EngagementRecord, IntakeRecord, UploadedFileMeta, _now  # noqa: F401

__all__ = [
    '_now',
    'EngagementRecord',
    'IntakeRecord',
    'UploadedFileMeta',
    'AuditResult',
    'FindingsRecord',
]
