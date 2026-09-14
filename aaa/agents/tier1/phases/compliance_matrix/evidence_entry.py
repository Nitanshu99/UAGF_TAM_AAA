"""The traceability record behind one article verdict: artefacts, URIs, controls, rationale."""
from __future__ import annotations

from aaa.agents.tier1.phases.compliance_matrix.fail_basis import finding_ref, ordered
from aaa.agents.tier1.phases.compliance_matrix.findings_by_article import _cgsa_controls_for
from aaa.agents.tier1.phases.compliance_matrix.parent_sub import relation_note
from aaa.agents.tier1.phases.compliance_matrix.rationale import (
    _exclusion_note,
    _rationale,
    _scope_note,
)
from aaa.agents.tier1.phases.compliance_matrix.scope_articles import scope_gate_articles
from aaa.agents.tier1.phases.compliance_matrix.supporting_tids import (
    _excluded_tids,
    _supporting_tids,
)
from aaa.platform.state.admission import admitted_artefacts

#: The artefact that carries the CGSA payload a control-level verdict rests on.
_CGSA_CARRIER = "T14_governance_findings"


def _with_cgsa_carrier(state: dict, tids: list[str], controls: list[str]) -> list[str]:
    """Add the governance-findings artefact when the verdict cites CGSA controls.

    Art. 5, 11, 14, 17 and 50 failed the 2026-09-12 Mariposa run on control
    scores (``Cnn: Score n below threshold m``) and T17 cited the control ids
    with no evidence URI at all — the payload those scores come from is T14,
    which the citation map never attributes to those articles. An admitted T14
    is therefore added here; a rejected one still admits nothing.
    """
    if not controls or _CGSA_CARRIER in tids or _CGSA_CARRIER not in admitted_artefacts(state):
        return tids
    return [*tids, _CGSA_CARRIER]


def _evidence_entry(state: dict, article: str, verdict: str,
                    art_findings: list[dict],
                    matrix: dict[str, str] | None = None) -> dict:
    """Build the traceability record for one article verdict.

    Only admitted artefacts reach ``supporting_template_ids`` and
    ``evidence_uris`` — which is what the T17 schema says both fields hold —
    and the rest are named in the rationale as excluded rather than dropped.

    :param matrix: The complete matrix, so a row can say how it relates to its
        parent article or its own paragraphs when they disagree (fix 43). Absent
        means no reconciliation is attempted, which is what a caller building one
        entry in isolation should get.
    """
    controls = _cgsa_controls_for(state, article)
    tids = _with_cgsa_carrier(state, _supporting_tids(state, article), controls)
    phase_artefacts = state.get("phase_artefacts", {})
    return {
        "supporting_template_ids": tids,
        "evidence_uris": [
            phase_artefacts[t].get("uri", "") for t in tids if t in phase_artefacts
        ],
        "cgsa_control_ids": controls,
        "finding_ids": [ref for ref in map(finding_ref, ordered(art_findings)) if ref],
        "rationale": (_rationale(verdict, tids, art_findings)
                      + relation_note(article, verdict, matrix or {})
                      + _scope_note(scope_gate_articles(state).get(article))
                      + _exclusion_note(_excluded_tids(state, article))),
    }


__all__ = ["_evidence_entry"]
