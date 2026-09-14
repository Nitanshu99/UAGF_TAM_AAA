"""Deterministic ISAE 3000-style auditor opinion for T18."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.report_architect.constants import METHODOLOGY_BASIS
from aaa.agents.tier2.report_architect.opinion.limitations import scope_limitation_text
from aaa.agents.tier2.report_architect.opinion.texts import build_paragraphs
from aaa.platform.state.verdicts import DISCLAIMER_OF_OPINION, FAIL, PASS

_SCOPE = (
    "The assessment covered admitted intake artefacts, phase reports, verifier "
    "critiques, the T17 compliance matrix, and CGSA handoff evidence available to "
    "UAGF-TAM at report generation time. It did not extend beyond evidence admitted "
    "to the audit evidence store."
)


def _opinion_type(decl: dict[str, Any], final_verdict: str,
                  material_count: int, material_ids: list[str]) -> str:
    """Decide the opinion type per the Phase 6 decision table.

    FAIL (confirmed non-conformity) → adverse; unverifiable mandatory
    requirement → disclaimer; otherwise unqualified / qualified by findings.

    ``final_verdict == DISCLAIMER_OF_OPINION`` is decisive on its own. It is
    derived from the same predicate as ``opinion_disclaimer``, but a declaration
    summary assembled outside Phase 6 (the HITL finalisation path) need not carry
    the flag, and the two fields disagreeing is finding F11 itself.
    """
    if decl.get("hitl_required") and not final_verdict:
        return "disclaimer_of_opinion"
    if final_verdict == FAIL:
        return "adverse"
    if final_verdict == DISCLAIMER_OF_OPINION or decl.get("opinion_disclaimer"):
        return "disclaimer_of_opinion"
    if final_verdict == PASS and material_count == 0 and not material_ids:
        return "unqualified"
    return "qualified"


def auditor_opinion(decl: dict[str, Any], final_verdict: str) -> dict[str, str]:
    """Build a deterministic ISAE 3000-style opinion block.

    :param decl: Declaration summary carrying findings and matrix state.
    :param final_verdict: The engagement's final verdict.
    :returns: Opinion block with type, paragraphs, methodology and scope.
    """
    material_count = int(decl.get("material_findings_count", 0) or 0)
    findings = decl.get("blocking_findings", []) or []
    material_ids = [str(f.get("finding_id", f.get("control_id", "finding")))
                    for f in findings
                    if f.get("materiality") in {"material", "possibly_material"}]
    opinion_type = _opinion_type(decl, final_verdict, material_count, material_ids)
    opinion, basis = build_paragraphs(opinion_type, decl, findings, material_ids)
    return {
        "opinion_type": opinion_type,
        "opinion_paragraph": opinion,
        "basis_paragraph": basis,
        "methodology_basis": METHODOLOGY_BASIS,
        "scope_paragraph": f"{_SCOPE} {scope_limitation_text(decl.get('scope_limitations'))}".strip(),
    }
