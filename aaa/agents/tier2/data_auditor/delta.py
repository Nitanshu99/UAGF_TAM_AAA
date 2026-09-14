"""State-delta assembly for the Phase 2 report."""
from __future__ import annotations

from typing import Any

from aaa.tools.findings import backfill_finding_evidence, collect_evidence_uris


def build_delta(ctx: dict[str, Any], uris: dict[str, str]) -> dict[str, Any]:
    """Assemble the state delta with findings, HITL flags, and artefacts."""
    findings, insufficient = ctx["findings"], ctx["insufficient"]
    special_cat_delta = ctx["special_cat_delta"]
    delta: dict[str, Any] = {
        "phase_artefacts": {
            tid: {"uri": uri, "sha256": "", "template_id": tid}
            for tid, uri in uris.items()
        },
    }
    evidence_pool = collect_evidence_uris(
        ctx["evidence_uris"], ctx["client_doc_hits"], list(uris.values()))
    backfill_finding_evidence(findings, evidence_pool)
    if findings:
        delta["blocking_findings"] = findings
    if insufficient:
        delta["insufficient_evidence_articles"] = sorted(insufficient)
    if special_cat_delta:
        delta["special_category_data"] = True
        delta["privacy_tier3_triggered"] = True
    material = any(f.get("materiality") == "material" for f in findings)
    if special_cat_delta or material or insufficient:
        reasons = []
        if special_cat_delta:
            reasons.append("undeclared special-category data detected (Privacy Tier-3 spawn)")
        if material:
            reasons.append("material data-governance finding(s) raised")
        if insufficient:
            reasons.append("dataset could not be independently verified: "
                           + ", ".join(sorted(insufficient)))
        delta["hitl_required"] = True
        delta["hitl_reason"] = "Phase 2 — " + "; ".join(reasons) + "."
    return delta
