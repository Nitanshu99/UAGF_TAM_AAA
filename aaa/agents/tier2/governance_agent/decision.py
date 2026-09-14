"""The Phase 5 human-review decision, computed once for T14 and for the report.

T14 hardcoded ``hitl_required: false`` while the Phase 5 report escalated on a
FAIL verdict, an unsatisfiable hard-constraint set, a risk-tier mismatch,
low-confidence controls, a T15 escalation, blocking follow-ups or material
reconciliation findings — so the governance artefact contradicted its own phase
(T-20260913-040). Every input here is known before T14 is stored.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.governance_agent.hitl import build_hitl_reason, has_blocking_followups
from aaa.agents.tier2.governance_agent.reconcile import reconcile_cgsa
from aaa.tools.cgsa_ingest import IngestResult


def phase5_hitl(result: IngestResult, t15: dict[str, Any],
                risk_tier_mismatch: bool) -> tuple[bool, str | None]:
    """Whether Phase 5 needs human review, and why.

    :param result: Validated CGSA ingest result (its payload is reconciled here).
    :param t15: The T15 artefact, which may carry its own escalation.
    :param risk_tier_mismatch: Phase 1 vs CGSA risk-tier disagreement.
    :returns: ``(required, reason or None)``.
    """
    verdict = result.state_delta.get("cgsa_phase5_verdict") or "PASS_WITH_OBSERVATIONS"
    csp_fail = result.state_delta.get("cgsa_csp_satisfiable") is False
    low_conf = len(result.low_confidence_controls) > 0
    followups = has_blocking_followups(result)
    payload = result.payload if isinstance(result.payload, dict) else {}
    recon_material = any(f.get("materiality") == "material" for f in reconcile_cgsa(payload))
    required = (verdict == "FAIL" or csp_fail or risk_tier_mismatch or low_conf
                or bool(t15.get("hitl_required")) or followups or recon_material)
    if not required:
        return False, None
    reason = build_hitl_reason(verdict, csp_fail, risk_tier_mismatch, low_conf, t15, result)
    extra = [text for flag, text in (
        (followups, "A CGSA follow-up is required before report completion."),
        (recon_material, "Reconciling the CGSA payload raised a material finding."),
    ) if flag]
    if extra and reason == "Phase 5 escalation.":
        reason = ""
    return True, " ".join(part for part in [reason, *extra] if part)


__all__ = ["phase5_hitl"]
