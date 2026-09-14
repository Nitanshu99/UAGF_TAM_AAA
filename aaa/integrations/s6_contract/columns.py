"""The sensitive-feature columns and domain scores S6 receives."""
from __future__ import annotations

from typing import Any

from aaa.tools.data_dictionary import explicit_data_dictionary

#: Findings that already state, in one sentence, why fairness could not be
#: scoped from the declared columns — reused rather than re-worded.
_FAIRNESS_SCOPE_FINDINGS = ("P3-DATADICT", "P4-FAIR-NA")


def _domain_scores(state: dict[str, Any]) -> dict[str, float]:
    """Governance domain scores keyed as the S4 sheet specifies.

    The sheet is explicit — *"key = domain_name, value = domain_score"* — while
    ``cgsa_domain_scores`` keys on ``"D1 Risk Management"``. Rebuilt from
    ``cgsa_payload.domains[]`` so the key is the canonical name S6 expects and
    its keyword match for *Transparency* / *Monitoring* cannot depend on the id
    prefix happening to be harmless.

    :param state: Audit state carrying ``cgsa_payload``.
    :returns: ``domain_name`` → ``domain_score``; empty when CGSA never ingested.
    """
    domains = (state.get("cgsa_payload") or {}).get("domains") or []
    return {str(d["domain_name"]): d["domain_score"] for d in domains
            if isinstance(d, dict) and d.get("domain_name") is not None
            and d.get("domain_score") is not None}
def _sensitive_feature_columns(state: dict[str, Any],
                               stage_b: dict[str, Any]) -> tuple[list[str], str | None]:
    """Resolve ``sensitive_feature_columns``, and why it is empty when it is.

    The S6 sheet's own contract: *"Empty list means fairness should be skipped
    with a clear reason."* Case 03 shipped ``null`` with the reason sitting one
    key over in ``blocking_findings`` (``P3-DATADICT`` — no column could be
    inferred; ``P4-FAIR-NA`` — group fairness does not apply to an anomaly
    model's output). Case 02, a limited-risk forecaster, has neither finding
    because Phase 4 was never scheduled for it at all — a different reason the
    findings list cannot state, since nothing in that phase ran to write one.

    :param state: Audit state carrying ``phase_plan``, ``phase_artefacts`` and
        ``blocking_findings``.
    :param stage_b: Stage B dossier dict.
    :returns: ``(columns, reason)`` — *reason* is ``None`` whenever *columns*
        is non-empty.
    """
    # Nested or top-level: reading the top level alone published an empty
    # sensitive-feature list to S6 for an engagement declaring five columns.
    block = explicit_data_dictionary(stage_b)
    columns = [str(c) for c in (block.get("sensitive_feature_columns") or [])]
    if columns:
        return columns, None
    if "T12_output_fairness_report" not in (state.get("phase_artefacts") or {}):
        p4_status = (state.get("phase_plan") or {}).get("P4")
        return [], (f"Phase 4 output-fairness testing was not run for this "
                    f"engagement (phase plan marks P4 {p4_status!r})." if p4_status
                    else "Phase 4 output-fairness testing did not run for this engagement.")
    finding = next((f for f in (state.get("blocking_findings") or [])
                    if f.get("finding_id") in _FAIRNESS_SCOPE_FINDINGS), None)
    if finding:
        return [], str(finding.get("description") or "")
    return [], "No sensitive_feature_columns were declared for this engagement."


__all__ = ["_domain_scores", "_sensitive_feature_columns"]
