"""The graph node: Art. 43 restatement, verdict derivation, KPIs and the final verdict."""
from __future__ import annotations

from typing import TYPE_CHECKING, cast

from aaa.agents.tier1.phases.compliance_matrix.derive_verdicts import _derive_verdicts
from aaa.agents.tier1.phases.compliance_matrix.finalise_verdict import _finalise_verdict
from aaa.agents.tier1.phases.compliance_matrix.logger import logger

if TYPE_CHECKING:
    from aaa.platform.state import AuditState


def node_compliance_matrix(state: dict) -> dict:
    """Compliance Matrix Assembly — §6 step 6."""
    from aaa.agents.tier1.phases.compliance_matrix.art43_restatement import (
        phase1_procedure,
        reconcile_art43,
    )
    from aaa.tools.art43_select import art43_select_from_state  # type: ignore
    from aaa.tools.completeness_score import compute_completeness_score
    from aaa.tools.regulatory_coverage import compute_regulatory_coverage_pct

    try:
        decided_in_phase_1 = phase1_procedure(state)
        art43 = art43_select_from_state(state, use_declared=False)
        state["art43_decision"] = {
            "procedure": art43["procedure"],
            "rationale": art43["rationale"],
        }
        # M11: T05 was decided in Phase 1, before `harmonised_standards_applied`
        # existed. Where the two disagree, say so rather than leaving a stale
        # artefact beside a fresher state field.
        reconcile_art43(state, decided_in_phase_1, state["art43_decision"])
    except Exception as exc:
        logger.warning("art43_select failed: %s", exc)

    _derive_verdicts(state)

    # Graph nodes receive a plain dict carrying the AuditState keys.
    compute_completeness_score(cast("AuditState", state))
    compute_regulatory_coverage_pct(cast("AuditState", state))

    _finalise_verdict(state)
    return state


__all__ = ["node_compliance_matrix"]
