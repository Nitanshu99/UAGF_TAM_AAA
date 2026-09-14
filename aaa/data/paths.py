"""
aaa.data.paths — Canonical data directory layout.

All data written by the persistence layer lives under a single root
(default: ``data/``, overridable via ``AAA_DATA_DIR``).

Layout
------
data/
  index.json                      — master index of all engagements
  inputs/
    <engagement_id>/
      engagement.json             — creation metadata entered by the user
      intake.json                 — Stage A / B / C payloads
      files.json                  — uploaded-file metadata (name, role, sha256, uri)
  results/
    <engagement_id>/
      audit_result.json           — final verdict + KPIs
      artefacts.json              — all phase artefact references (T01a–T18)
      findings.json               — blocking / positive findings + remediation roadmap
      compliance_matrix.json      — article → verdict map
  customer/
    <normalized_company_name>/
      <engagement_id>_audit_state.json   — full final AuditState
      <engagement_id>_T17.json           — T17 compliance matrix payload
      <engagement_id>_T18.json           — T18 audit report payload
"""
from __future__ import annotations

import os
from pathlib import Path


def _data_root() -> Path:
    """Return the data root dir, resolved at call time so tests can monkeypatch."""
    from aaa.settings import settings
    return Path(os.environ.get("AAA_DATA_DIR", settings.aaa_data_dir))


# ── Sub-directory helpers ─────────────────────────────────────────────────────

def inputs_dir(engagement_id: str) -> Path:
    """``data/inputs/<engagement_id>/`` — user-entered data."""
    return _data_root() / "inputs" / engagement_id


def results_dir(engagement_id: str) -> Path:
    """``data/results/<engagement_id>/`` — audit end results."""
    return _data_root() / "results" / engagement_id


def customer_dir(company_slug: str) -> Path:
    """``data/customer/<normalized_company_name>/`` — per-company deliverables."""
    return _data_root() / "customer" / company_slug


def index_path() -> Path:
    """``data/index.json`` — master engagement index."""
    return _data_root() / "index.json"


# ── File-name constants ────────────────────────────────────────────────────────

ENGAGEMENT_FILE  = "engagement.json"
INTAKE_FILE      = "intake.json"
FILES_META_FILE  = "files.json"
AUDIT_RESULT_FILE     = "audit_result.json"
ARTEFACTS_FILE        = "artefacts.json"
FINDINGS_FILE         = "findings.json"
COMPLIANCE_MATRIX_FILE = "compliance_matrix.json"


__all__ = [
    "inputs_dir",
    "results_dir",
    "customer_dir",
    "index_path",
    "ENGAGEMENT_FILE",
    "INTAKE_FILE",
    "FILES_META_FILE",
    "AUDIT_RESULT_FILE",
    "ARTEFACTS_FILE",
    "FINDINGS_FILE",
    "COMPLIANCE_MATRIX_FILE",
]
