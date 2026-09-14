"""A provider issue raised on a report whose procedure measured nothing is an evidence gap.

T11 holds nothing but the robustness probe's results. When no model was supplied the
probe ran on nothing, and case 06's Verifier still raised two material provider
non-conformities on T11 ("no probes executed ... for a high-risk system under Art. 15"),
failing Art. 15 on an absent measurement (MiniMax run, 2026-09-14). An unperformed
measurement leaves the article unassessed; it cannot show the requirement unmet.

T12 and T13 hold only Phase 4's output measurements. Case 06's CLI run had the Verifier
type T13's "no output sample was inspected … the Art. 10§2(f) bias examination of
system outputs is therefore unassessed" as a material provider non-conformity, failing
Art. 10§2(f) where the wizard run of the same case left it INSUFFICIENT_EVIDENCE
(T-20260914-063). Phase 4 records that it measured nothing as ``P4-NOT-TESTED``.
"""
from __future__ import annotations

from typing import Any

from aaa.platform.audit_programme.procedures import PERFORMED, PROGRAMME

#: Reports that record one programme procedure's measurements and nothing else.
MEASUREMENT_ONLY = {"T11_robustness_report": "robustness_probe"}

#: Reports that record Phase 4's measurements, and the finding Phase 4 raises when it made none.
NOT_TESTED_FINDING = {"T12_output_fairness_report": "P4-NOT-TESTED",
                      "T13_output_sampling_log": "P4-NOT-TESTED"}


def _unmeasured(tid: str, state: dict[str, Any]) -> str | None:
    """Why *tid*'s report measured nothing, or ``None`` when it measured (or is not such a report)."""
    procedure = MEASUREMENT_ONLY.get(tid)
    record = (state.get("procedure_outcomes") or {}).get(procedure or "")
    if procedure and isinstance(record, dict) and record.get("outcome") != PERFORMED:
        return (f"{PROGRAMME[procedure].title.lower()} was not performed "
                f"({record.get('reason') or 'no reason recorded'})")
    wanted = NOT_TESTED_FINDING.get(tid)
    hit = next((f for f in state.get("blocking_findings") or []
                if isinstance(f, dict) and wanted and f.get("finding_id") == wanted), None)
    return f"{wanted} records that nothing was measured ({hit.get('description')})" if hit else None


def as_measured(issue: dict[str, Any], tid: str, state: dict[str, Any]) -> dict[str, Any]:
    """*issue*, or the same issue as an evidence gap when *tid*'s report measured nothing.

    :param issue: A carried Verifier issue.
    :param tid: The template it was raised on.
    :param state: Audit state carrying ``procedure_outcomes`` and ``blocking_findings``.
    """
    if issue.get("issue_type") != "provider_nonconformity":
        return issue
    reason = _unmeasured(tid, state)
    if reason is None:
        return issue
    return {**issue, "issue_type": "evidence_gap", "description": (
        f"{issue.get('description')} Recorded as an evidence gap: {reason}, so the report "
        "measured nothing that could establish a non-conformity.")}


__all__ = ["MEASUREMENT_ONLY", "NOT_TESTED_FINDING", "as_measured"]
