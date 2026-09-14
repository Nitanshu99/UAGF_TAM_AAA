"""The run manifest: what the run was, and whether a model was actually called."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

#: Deliverables copied into each run's folder, by filename suffix.
_ARCHIVED = ("_audit_state.json", "_T17.json", "_T18.json", "_audit_report.pdf",
             "_client_report.md", "_client_brief.pdf", "_hitl_review.json")
def _model_actually_called(engagement_id: str) -> str | None:
    """The model this engagement's calls were made against, from the audit trail.

    Read rather than resolved. ``resolve_model`` answers "what would this
    process choose *now*", which is the same thing only while the environment
    has not moved — and the first archive written got that wrong, labelling a
    GLM-5.3-Flash run as Nemotron because the archiving process did not carry
    the ``OPENROUTER_MODEL`` the run had. The trail records what was called.
    """
    from aaa.observability.llm_audit import record
    path = Path(getattr(record, "_AUDIT_JSONL", "logs/audit/llm_audit.jsonl"))
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("engagement_id") == engagement_id and entry.get("model"):
            return str(entry["model"])
    return None
def _manifest(state: dict[str, Any], engagement_id: str) -> dict[str, Any]:
    """What produced this run — enough to tell two runs apart without diffing them."""
    from aaa.platform.model_registry import active_provider, resolve_model
    integrity = state.get("run_integrity") or {}
    return {
        "engagement_id": engagement_id,
        "archived_at": datetime.now(timezone.utc).isoformat(),
        "run_id": integrity.get("run_id"),
        "code_revision": integrity.get("code_revision"),
        "provider": active_provider(),
        "model": _model_actually_called(engagement_id) or resolve_model("ReportArchitect", None),
        "final_verdict": state.get("final_verdict"),
        "intake_completeness_score": state.get("intake_completeness_score"),
        "completeness_score": state.get("completeness_score"),
        "regulatory_coverage_pct": state.get("regulatory_coverage_pct"),
        "compliance_matrix": state.get("compliance_matrix") or {},
        "blocking_findings_count": len(state.get("blocking_findings") or []),
        "suitable_for_handoff": integrity.get("suitable_for_handoff"),
        "fallback_critique_ids": integrity.get("fallback_critique_ids") or [],
        "fallback_authored_phases": integrity.get("fallback_authored_phases") or [],
        "unadmitted_artefacts": [entry.get("template_id")
                                 for entry in (state.get("unadmitted_artefacts") or [])],
    }


__all__ = ["_ARCHIVED", "_manifest", "_model_actually_called"]
