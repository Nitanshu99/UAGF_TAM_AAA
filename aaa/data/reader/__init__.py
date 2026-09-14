"""aaa.data.reader — Read persisted user data and audit results from the data/ folder.

All functions return plain dicts (suitable for JSON serialisation by FastAPI)
or ``None`` / empty list when the requested data does not exist.

Public functions
----------------
load_engagement(eid)        → dict | None   — engagement creation metadata
load_intake(eid)            → dict | None   — Stage A/B/C payloads
load_uploaded_files(eid)    → list[dict]    — uploaded-file metadata list
load_audit_result(eid)      → dict | None   — final verdict + KPIs
load_artefacts(eid)         → dict | None   — phase artefact URI map
load_findings(eid)          → dict | None   — blocking / positive + remediation
load_compliance_matrix(eid) → dict | None   — article → verdict map
load_full_result(eid)       → dict | None   — all four result files merged
list_engagements()          → list[dict]    — index summary, newest-first
list_results()              → list[dict]    — only completed engagements"""
from aaa.data.reader.load_full_result import (  # noqa: F401
    list_engagements,
    list_results,
    load_full_result,
)
from aaa.data.reader.logger import (  # noqa: F401
    _read_json,
    load_artefacts,
    load_audit_result,
    load_compliance_matrix,
    load_engagement,
    load_findings,
    load_intake,
    load_uploaded_files,
    logger,
)

__all__ = [
    'logger',
    '_read_json',
    'load_engagement',
    'load_intake',
    'load_uploaded_files',
    'load_audit_result',
    'load_artefacts',
    'load_findings',
    'load_compliance_matrix',
    'load_full_result',
    'list_engagements',
    'list_results',
]
