"""
aaa.agents.tier1.phases.compliance_matrix — Compliance matrix assembly node.

Single exported function: ``node_compliance_matrix(state)``.

Derives each EU AI Act article verdict from *actual evidence* — phase findings,
the independent-verifier critiques, and per-article insufficient-evidence signals —
instead of the previous behaviour of stamping every admitted article ``PASS``.

Verdict precedence per article:
  1. a confirmed material non-conformity finding   → FAIL
  2. required independent analysis not performed    → INSUFFICIENT_EVIDENCE
  3. a qualifying (possibly-material/observation)   → PASS_WITH_OBSERVATIONS
  4. admitted, verifier-accepted, no findings       → PASS
  5. referenced but no admitted evidence            → INSUFFICIENT_EVIDENCE

It also builds ``state['article_evidence']`` (rationale + evidence URIs + supporting
template ids + CGSA control ids + finding ids per article) so the T17 compliance
matrix is traceable, and computes the final verdict + opinion-disclaimer flag.
"""
from __future__ import annotations

import logging

from aaa.tools.findings import articles_for

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

_ADMITTED_VERDICTS = {"accept", "accept_with_notes"}

# Mandatory high-risk requirements: INSUFFICIENT_EVIDENCE on any of these means the
# auditor cannot conclude conformity → disclaimer of opinion (§WS5/WS7).
_CORE_HIGH_RISK_ARTICLES = {
    "Art.9", "Art.10", "Art.11", "Art.12", "Art.13", "Art.14", "Art.15", "Art.17",
}


def _core_article(article: str) -> str:
    """Reduce an article reference to its base form (``Art.15§1`` → ``Art.15``)."""
    base = article.split("§", 1)[0]
    base = base.split(" point", 1)[0]
    return base.strip()


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
        if critique.get("verdict") in _ADMITTED_VERDICTS:
            for art in critique.get("article_citations", []):
                admitted.add(art)
            if tid in _TEMPLATE_ARTICLES:
                admitted.update(_TEMPLATE_ARTICLES[tid])

    if "T01b_annex_iv_dossier" in state.get("phase_artefacts", {}):
        admitted.update({"Art.11", "Annex_IV"})
    if "T01c_intake_completeness_report" in state.get("phase_artefacts", {}):
        admitted.add("Annex_IV")

    return admitted


def _findings_by_article(state: dict) -> dict[str, list[dict]]:
    """Index blocking findings (phase + CGSA) by the articles they map to."""
    index: dict[str, list[dict]] = {}
    sources = list(state.get("blocking_findings", []) or [])
    for f in state.get("cgsa_blocking_findings", []) or []:
        # CGSA gaps carry their own severity; treat critical/major as material.
        sev = str(f.get("gap_severity", "")).lower()
        materiality = "material" if sev in {"critical", "major", "high"} else "possibly_material"
        sources.append({**f, "materiality": f.get("materiality", materiality)})
    for f in sources:
        for art in articles_for(f):
            index.setdefault(art, []).append(f)
            base = _core_article(art)
            if base != art:
                index.setdefault(base, []).append(f)
    return index


def _cgsa_controls_for(state: dict, article: str) -> list[str]:
    """Return CGSA control ids mapped to an article, if the payload provides them."""
    payload = state.get("cgsa_payload") or {}
    matrix = payload.get("eu_ai_act_compliance_matrix") or {}
    base = _core_article(article)
    key = "article_" + base.replace("Art.", "").strip()
    entry = matrix.get(key) or {}
    return list(entry.get("controls_mapped", []) or [])


def _supporting_tids(state: dict, article: str) -> list[str]:
    """Accepted template ids that evidence an article (via citations + template map)."""
    tids: list[str] = []
    for tid, crit in state.get("verifier_critiques", {}).items():
        if crit.get("verdict") not in _ADMITTED_VERDICTS:
            continue
        if article in (crit.get("article_citations") or []):
            tids.append(tid)
    for tid, arts in _TEMPLATE_ARTICLES.items():
        if article in arts and tid in state.get("phase_artefacts", {}) and tid not in tids:
            tids.append(tid)
    return tids


def _derive_verdicts(state: dict) -> None:
    """Populate ``compliance_matrix`` + ``article_evidence`` from evidence."""
    admitted = _collect_admitted_articles(state)
    insufficient = set(state.get("insufficient_evidence_articles", []) or [])
    fba = _findings_by_article(state)

    all_articles = set(admitted) | set(insufficient) | set(fba.keys())
    # Preserve any verdicts already set deterministically (e.g., scope gate FAILs).
    preset = {a: v for a, v in state.get("compliance_matrix", {}).items()
              if v not in (None, "PENDING")}

    matrix: dict[str, str] = {}
    evidence: dict[str, dict] = {}
    phase_artefacts = state.get("phase_artefacts", {})

    for article in sorted(all_articles):
        if article in preset:
            matrix[article] = preset[article]
        else:
            art_findings = fba.get(article, [])
            has_material = any(f.get("materiality") == "material" for f in art_findings)
            has_qual = any(
                f.get("materiality") in {"possibly_material", "observation"}
                for f in art_findings
            )
            is_insufficient = article in insufficient or _core_article(article) in insufficient
            if has_material:
                verdict = "FAIL"
            elif is_insufficient:
                verdict = "INSUFFICIENT_EVIDENCE"
            elif has_qual:
                verdict = "PASS_WITH_OBSERVATIONS"
            elif article in admitted:
                verdict = "PASS"
            else:
                verdict = "INSUFFICIENT_EVIDENCE"
            matrix[article] = verdict

        tids = _supporting_tids(state, article)
        art_findings = fba.get(article, [])
        evidence[article] = {
            "supporting_template_ids": tids,
            "evidence_uris": [
                phase_artefacts[t].get("uri", "") for t in tids if t in phase_artefacts
            ],
            "cgsa_control_ids": _cgsa_controls_for(state, article),
            "finding_ids": [str(f.get("finding_id", "")) for f in art_findings if f.get("finding_id")],
            "rationale": _rationale(matrix[article], tids, art_findings),
        }

    state["compliance_matrix"] = matrix
    state["article_evidence"] = evidence


def _rationale(verdict: str, tids: list[str], findings: list[dict]) -> str:
    """One-sentence justification for an article verdict."""
    descs = "; ".join(str(f.get("description", "")) for f in findings)[:300]
    if verdict == "FAIL":
        return f"Material non-conformity from independent analysis: {descs or 'see findings register'}."
    if verdict == "INSUFFICIENT_EVIDENCE":
        return (
            f"Required independent verification could not be performed: "
            f"{descs or 'no admitted evidence for this article'}."
        )
    if verdict == "PASS_WITH_OBSERVATIONS":
        return (
            f"Admitted evidence ({', '.join(tids) or 'phase artefacts'}) with observations: "
            f"{descs or 'minor observations noted'}."
        )
    return (
        f"Admitted, verifier-accepted evidence ({', '.join(tids) or 'phase artefacts'}) "
        "with no findings raised."
    )


def _compute_final_verdict(state: dict) -> str:
    """Apply the evidence-grounded verdict ladder and set the opinion-disclaimer flag."""
    verdicts = set(state.get("compliance_matrix", {}).values())
    phase5_fail = state.get("cgsa_phase5_verdict") == "FAIL"
    csp_fail = state.get("cgsa_csp_satisfiable") is False

    core_insufficient = any(
        v == "INSUFFICIENT_EVIDENCE" and _core_article(a) in _CORE_HIGH_RISK_ARTICLES
        for a, v in state.get("compliance_matrix", {}).items()
    )

    if "FAIL" in verdicts or phase5_fail or csp_fail:
        state["opinion_disclaimer"] = False
        return "FAIL"

    # Cannot conclude conformity on a mandatory high-risk requirement → disclaimer.
    state["opinion_disclaimer"] = bool(core_insufficient)

    if "INSUFFICIENT_EVIDENCE" in verdicts or "PASS_WITH_OBSERVATIONS" in verdicts:
        return "PASS_WITH_OBSERVATIONS"

    cs = state.get("completeness_score") or 0.0
    rc = state.get("regulatory_coverage_pct") or 0.0
    ics = state.get("intake_completeness_score") or 0.0
    if ics >= 0.90 and cs >= 0.90 and rc >= 90.0:
        return "PASS"
    if ics >= 0.80 and cs >= 0.75 and rc >= 75.0:
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

    _derive_verdicts(state)

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
        "Engagement %s final_verdict=%s (cs=%.2f rc=%.1f, disclaimer=%s)",
        state["engagement_id"],
        verdict,
        state.get("completeness_score") or 0.0,
        state.get("regulatory_coverage_pct") or 0.0,
        state.get("opinion_disclaimer"),
    )
    return state


__all__ = ["node_compliance_matrix"]
