"""HITL-escalation reasoning helpers for Phase 5."""
from __future__ import annotations

from typing import Any

from aaa.tools.cgsa_ingest import IngestResult
from aaa.tools.cgsa_ingest.logger import _LOW_CONFIDENCE_THRESHOLD


def has_blocking_followups(result: IngestResult) -> bool:
    """True if any CGSA follow-up has ``urgency=required_before_report_completion``.

    :param result: CGSA ingest result.
    """
    for item in result.state_delta.get("cgsa_recommended_follow_up", []) or []:
        if item.get("urgency") == "required_before_report_completion":
            return True
    return False


def low_confidence_reason(controls: list[dict[str, Any]]) -> str:
    """Name each low-confidence control with its own confidence.

    The list merges controls the self-assessment flagged itself with those below
    the ingest threshold, and the reason once stated "(<0.60)" for all of them —
    beside C15 at 0.65 and C21 at 0.70 (case 04, T-20260913-077).

    :param controls: ``IngestResult.low_confidence_controls``.
    """
    named = ", ".join(
        f"{c.get('control_id')} ({c['confidence']:.2f})" if isinstance(c.get("confidence"), (int, float))
        else str(c.get("control_id")) for c in controls)
    return (f"{len(controls)} CGSA control(s) flagged low-confidence by the self-assessment or "
            f"below the {_LOW_CONFIDENCE_THRESHOLD:.2f} ingest threshold: {named}.")


def build_hitl_reason(
    phase5_verdict: str,
    csp_fail: bool,
    risk_tier_mismatch: bool,
    low_conf: bool,
    t15: dict[str, Any],
    result: IngestResult,
) -> str:
    """Compose a human-readable HITL reason string.

    :param phase5_verdict: Verdict lifted from the CGSA hand-off.
    :param csp_fail: Hard-constraint solver failure flag.
    :param risk_tier_mismatch: Phase 1 vs CGSA risk-tier disagreement.
    :param low_conf: Low-confidence controls present.
    :param t15: T15 artefact (may carry its own escalation).
    :param result: CGSA ingest result.
    :returns: Space-joined reason sentences.
    """
    reasons: list[str] = []
    if phase5_verdict == "FAIL":
        reasons.append("Phase 5 verdict is FAIL.")
    if csp_fail:
        reasons.append("CGSA csp_satisfiable=false (hard-constraint violation).")
    if risk_tier_mismatch:
        reasons.append("Phase 1 risk_tier disagrees with CGSA metadata.risk_tier.")
    if low_conf:
        reasons.append(low_confidence_reason(result.low_confidence_controls))
    if t15.get("hitl_required"):
        reasons.append(t15.get("hitl_reason") or "Ops review escalation.")
    if not reasons:
        reasons.append("Phase 5 escalation.")
    return " ".join(reasons)
