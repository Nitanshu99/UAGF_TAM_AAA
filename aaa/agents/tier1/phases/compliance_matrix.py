"""
aaa.agents.tier1.phases.compliance_matrix — Compliance matrix assembly node.

Single exported function: ``node_compliance_matrix(state)``.

Assembles article verdicts from phase artefacts + CGSA payload,
computes KPI 1 (completeness_score) and KPI 2 (regulatory_coverage_pct),
and determines the final_verdict.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Template → article mapping for compliance matrix assembly
_TEMPLATE_ARTICLES: dict[str, list[str]] = {
    "T01b_annex_iv_dossier":           ["Art.11", "Annex_IV"],
    "T01c_intake_completeness_report":  ["Annex_IV"],
    "T02_system_card":                  ["Art.5", "Art.13"],
    "T03_annex_iii_mapping":            ["Art.6", "Annex_III"],
    "T04_risk_tier_decision":           ["Art.5", "Art.6"],
    "T05_art43_decision":               ["Art.43"],
    "T06_datasheet_for_datasets":       ["Art.10"],
    "T09_model_card":                   ["Art.13"],
    "T11_robustness_report":            ["Art.15"],
    "T12_output_fairness_report":       ["Art.15", "Art.50"],
    "T13_output_sampling_log":          ["Art.50"],
    "T14_governance_findings":          ["Art.9", "Art.17"],
    "T15_monitoring_logging_review":    ["Art.12", "Art.72"],
    "T17_compliance_matrix":            ["Art.17"],
}


def _collect_admitted_articles(state: dict) -> set[str]:
    """Collect all articles admitted via scope gate flags and verifier critiques."""
    admitted: set[str] = set()

    gate = state.get("scope_gate", {})
    if gate.get("become_provider_under_art25"):
        admitted.add("Art.25")
    if gate.get("triggers_fria"):
        admitted.add("Art.27")
    if gate.get("triggers_art50_transparency"):
        admitted.add("Art.50")
    if gate.get("is_gpai_systemic"):
        admitted.add("Arts.51-55")

    for tid, critique in state.get("verifier_critiques", {}).items():
        if critique.get("verdict") in {"accept", "accept_with_notes"}:
            for art in critique.get("article_citations", []):
                admitted.add(art)
            if tid in _TEMPLATE_ARTICLES:
                admitted.update(_TEMPLATE_ARTICLES[tid])

    if "T01b_annex_iv_dossier" in state.get("phase_artefacts", {}):
        admitted.update({"Art.11", "Annex_IV"})
    if "T01c_intake_completeness_report" in state.get("phase_artefacts", {}):
        admitted.add("Annex_IV")

    return admitted


def _compute_final_verdict(state: dict) -> str:
    """Apply the three-tier verdict ladder."""
    phase5_ok = state.get("cgsa_phase5_verdict") in {"PASS", "PASS_WITH_OBSERVATIONS", None}
    csp_ok = state.get("cgsa_csp_satisfiable", True) is not False
    cs = state.get("completeness_score") or 0.0
    rc = state.get("regulatory_coverage_pct") or 0.0
    ics = state.get("intake_completeness_score") or 0.0

    if ics >= 0.90 and cs >= 0.90 and rc >= 90.0 and phase5_ok and csp_ok:
        return "PASS"
    if ics >= 0.80 and cs >= 0.75 and rc >= 75.0 and phase5_ok and csp_ok:
        return "PASS_WITH_OBSERVATIONS"
    return "FAIL"


def node_compliance_matrix(state: dict) -> dict:
    """Compliance Matrix Assembly — §6 step 6."""
    from aaa.tools.art43_select import art43_select_from_state  # type: ignore
    from aaa.tools.completeness_score import compute_completeness_score
    from aaa.tools.regulatory_coverage import compute_regulatory_coverage_pct

    try:
        art43 = art43_select_from_state(state, use_declared=False)
        state["art43_decision"] = {
            "procedure": art43["procedure"],
            "rationale": art43["rationale"],
        }
    except Exception as exc:
        logger.warning("art43_select failed: %s", exc)

    for article in _collect_admitted_articles(state):
        if state["compliance_matrix"].get(article) in (None, "PENDING"):
            state["compliance_matrix"][article] = "PASS"

    compute_completeness_score(state)
    compute_regulatory_coverage_pct(state)

    verdict = _compute_final_verdict(state)
    state["final_verdict"] = verdict
    state["material_findings_count"] = sum(
        1 for f in state.get("blocking_findings", [])
        if f.get("materiality") == "material"
    )
    state["possibly_material_findings_count"] = sum(
        1 for f in state.get("blocking_findings", [])
        if f.get("materiality") == "possibly_material"
    )
    logger.info(
        "Engagement %s final_verdict=%s (cs=%.2f rc=%.1f)",
        state["engagement_id"],
        verdict,
        state.get("completeness_score") or 0.0,
        state.get("regulatory_coverage_pct") or 0.0,
    )
    return state


__all__ = ["node_compliance_matrix"]
