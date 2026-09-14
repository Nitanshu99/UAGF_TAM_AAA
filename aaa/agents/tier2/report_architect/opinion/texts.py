"""Opinion and basis paragraph builders for the ISAE 3000-style opinion."""
from __future__ import annotations

from typing import Any


def build_paragraphs(
    opinion_type: str,
    decl: dict[str, Any],
    findings: list[dict[str, Any]],
    material_ids: list[str],
) -> tuple[str, str]:
    """Compose the opinion and basis paragraphs for the given opinion type.

    :param opinion_type: One of ``unqualified`` / ``qualified`` / ``adverse``
        / ``disclaimer_of_opinion``.
    :param decl: Declaration summary carrying findings and matrix state.
    :param findings: Blocking findings from the engagement.
    :param material_ids: Finding ids with material / possibly-material weight.
    :returns: ``(opinion_paragraph, basis_paragraph)``.
    """
    system_name = (decl.get("stage_a") or {}).get("system_name") or "the AI system"
    matrix = decl.get("compliance_matrix", {}) or {}
    if opinion_type == "unqualified":
        return (
            f"In our opinion, based on the procedures performed, {system_name} was, "
            "in all material respects, designed and documented in conformity with the "
            "applicable EU AI Act requirements assessed by UAGF-TAM.",
            "No material findings were identified from independently verified evidence.")
    if opinion_type == "qualified":
        observations = [f for f in findings
                        if f.get("materiality") in {"possibly_material", "observation"}]
        obs_summary = "; ".join(
            f"{f.get('finding_id', 'finding')}: {f.get('description', '')}"
            for f in observations[:5])
        return (
            f"Except for the matters described in the Basis for Conclusion, {system_name} "
            "was designed and documented in conformity with the applicable EU AI Act "
            "requirements assessed by UAGF-TAM.",
            "Qualified matters: "
            f"{obs_summary or (', '.join(material_ids) if material_ids else 'see findings register')}.")
    if opinion_type == "adverse":
        fail_articles = sorted(a for a, v in matrix.items() if v == "FAIL")
        return (
            "In our opinion, due to the significance of the matters described in the "
            f"Basis for Conclusion, {system_name} is not in conformity with the applicable "
            "EU AI Act requirements assessed by UAGF-TAM.",
            "The final audit verdict is FAIL. Confirmed non-conformities on: "
            f"{', '.join(fail_articles) or 'see findings register'}.")
    insufficient = sorted(a for a, v in matrix.items() if v == "INSUFFICIENT_EVIDENCE")
    return (
        f"We do not express an assurance conclusion on {system_name} because sufficient "
        "appropriate evidence was not available to verify mandatory high-risk requirements.",
        ("Independent verification could not be performed for: "
         f"{', '.join(insufficient) or 'core high-risk requirements'}. "
         + str(decl.get("hitl_reason") or "")).strip())
