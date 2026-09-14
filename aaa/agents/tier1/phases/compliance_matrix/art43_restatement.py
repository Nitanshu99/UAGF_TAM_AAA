"""Reconcile the stored Art. 43 artefact with the post-Phase-5 recomputation (M11).

``T05_art43_decision`` is written once, by the ScopeAgent, in Phase 1.
``harmonised_standards_applied`` is set by Phase 5, from the CGSA — two phases
later — so Phase 1 decides on a value it cannot yet have and
``scope_agent.diffing.decide_art43`` passed a literal ``False`` to say so.

``node_compliance_matrix`` then recomputes ``state["art43_decision"]`` from the
real state, and *that* is what reaches T18, the PDF and ``audit_result.json``.
Nothing rewrote T05. Two Art. 43 decisions therefore existed in every
engagement, derived from different values of the same field, and on an Annex III
point 1 system they disagree about whether a notified body is required — the
most consequential binary the system emits.

The artefact cannot be re-issued from here: this node is handed the state and
not the evidence store. What it can do is refuse to let the two diverge
silently. The recomputed decision stays authoritative, the artefact is recorded
as superseded, and a finding names both procedures so a human sees the conflict
rather than inheriting whichever field they happened to read.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.phases.compliance_matrix.logger import logger
from aaa.tools.findings import make_finding


def phase1_procedure(state: dict[str, Any]) -> str | None:
    """The Art. 43 procedure Phase 1 decided, read before it is overwritten.

    The ScopeAgent writes it to ``state["art43_decision"]`` through its
    ``declaration_verification_delta``, and it is the same value it stored in
    ``T05``. The stored ``ArtefactRef`` itself carries only ``uri``, ``sha256``
    and ``template_id``, so the artefact is not the place to read it from.

    :param state: The AuditState, before the recomputation overwrites the key.
    :returns: The Phase 1 procedure, or ``None`` when Phase 1 recorded none.
    """
    decision = state.get("art43_decision")
    if not isinstance(decision, dict):
        return None
    procedure = decision.get("procedure")
    return str(procedure) if procedure else None


def reconcile_art43(state: dict[str, Any], phase1: str | None,
                    recomputed: dict[str, Any]) -> None:
    """Record any disagreement between T05 and the recomputed decision.

    :param state: The mutable AuditState; gains ``art43_supersedes_t05`` and,
        on a disagreement, a blocking-eligible finding.
    :param phase1: The procedure Phase 1 decided, from :func:`phase1_procedure`.
    :param recomputed: The decision just produced from the post-Phase-5 state.
    """
    final = recomputed.get("procedure")
    if phase1 is None or phase1 == final:
        return
    state["art43_supersedes_t05"] = {"phase1_procedure": phase1, "final_procedure": final}
    logger.warning(
        "Art. 43: T05 recorded %r in Phase 1 and the post-Phase-5 state resolves "
        "to %r. The recomputed decision is authoritative; T05 is superseded.",
        phase1, final)
    state.setdefault("findings", []).append(make_finding(
        finding_id="ART43-SUPERSEDED",
        description=(
            f"The stored Art. 43 decision (T05) records {phase1!r}, decided in "
            f"Phase 1 before harmonised_standards_applied was known. Recomputing "
            f"from the completed state gives {final!r}. The recomputed procedure "
            f"is the one carried by the report; T05 is superseded and must not be "
            f"relied on for the conformity route."),
        materiality="material",
        articles=["Art.43"],
        source_phase="compliance_matrix",
        recommendation=(
            "Re-issue T05 from the completed state, or move the Art. 43 decision "
            "to a point after the CGSA has been ingested."),
        declared=phase1,
        observed=final,
    ))
