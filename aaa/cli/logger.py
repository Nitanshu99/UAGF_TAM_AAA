"""Part 1 of the former ``cli`` module (auto-split)."""
from __future__ import annotations

import json
import logging
import pathlib

logger = logging.getLogger("aaa.cli")


def _load_json(path: pathlib.Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


def _summarise(final: dict) -> dict:
    """Return a stdout-friendly summary of the final AuditState."""
    artefacts = final.get("phase_artefacts", {}) or {}
    return {
        "engagement_id": final.get("engagement_id"),
        "final_verdict": final.get("final_verdict"),
        "intake_completeness_score": final.get("intake_completeness_score"),
        "completeness_score": final.get("completeness_score"),
        "regulatory_coverage_pct": final.get("regulatory_coverage_pct"),
        "art43_decision": final.get("art43_decision"),
        "hitl_required": final.get("hitl_required", False),
        "hitl_reason": final.get("hitl_reason"),
        "phase_artefacts": {
            tid: (ref.get("uri") if isinstance(ref, dict) else None)
            for tid, ref in artefacts.items()
        },
        "compliance_matrix": final.get("compliance_matrix", {}),
        "blocking_findings_count": len(final.get("blocking_findings") or []),
        "positive_findings_count": len(final.get("positive_findings") or []),
    }
