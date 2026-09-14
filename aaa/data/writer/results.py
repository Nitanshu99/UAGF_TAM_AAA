"""Persist the audit result files after the pipeline completes."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from aaa.data import index as idx
from aaa.data import models, paths
from aaa.data.writer.atomic import _write
from aaa.platform.state.verdicts import DISCLAIMER_OF_OPINION

logger = logging.getLogger(__name__)


def _build_audit_result(engagement_id: str, final_state: dict[str, Any],
                        completed_at: str) -> "models.AuditResult":
    """Map the final AuditState onto the persisted result record."""
    art43 = final_state.get("art43_decision") or {}
    return models.AuditResult(
        engagement_id=engagement_id,
        final_verdict=final_state.get("final_verdict") or DISCLAIMER_OF_OPINION,
        intake_completeness_score=final_state.get("intake_completeness_score"),
        completeness_score=final_state.get("completeness_score"),
        regulatory_coverage_pct=final_state.get("regulatory_coverage_pct"),
        material_findings_count=final_state.get("material_findings_count"),
        possibly_material_findings_count=final_state.get("possibly_material_findings_count"),
        auditor_opinion=final_state.get("auditor_opinion"),
        art43_procedure=art43.get("procedure") if isinstance(art43, dict) else None,
        completed_at=completed_at,
    )


def save_result(engagement_id: str, final_state: dict[str, Any]) -> None:
    """Persist the full audit result under ``data/results/<id>/``.

    Writes ``audit_result.json`` (verdict + KPIs), ``artefacts.json``,
    ``findings.json`` and ``compliance_matrix.json``, and updates the master
    index with the final verdict and completion time.

    :param engagement_id: Engagement identifier.
    :param final_state: Final ``AuditState`` from the Orchestrator.
    """
    completed_at = datetime.now(timezone.utc).isoformat()
    result = _build_audit_result(engagement_id, final_state, completed_at)
    rdir = paths.results_dir(engagement_id)
    _write(rdir / paths.AUDIT_RESULT_FILE, result.to_dict())
    _write(rdir / paths.ARTEFACTS_FILE, final_state.get("phase_artefacts") or {})
    findings = models.FindingsRecord(
        engagement_id=engagement_id,
        blocking_findings=final_state.get("blocking_findings") or [],
        positive_findings=final_state.get("positive_findings") or [],
        remediation_roadmap=final_state.get("remediation_roadmap") or [],
        recorded_at=completed_at,
    )
    _write(rdir / paths.FINDINGS_FILE, findings.to_dict())
    _write(rdir / paths.COMPLIANCE_MATRIX_FILE, final_state.get("compliance_matrix") or {})
    idx.upsert({
        "engagement_id": engagement_id, "status": "completed",
        "final_verdict": result.final_verdict, "completed_at": completed_at,
    })
    logger.info("Saved audit result: %s → verdict=%s", engagement_id, result.final_verdict)
