"""A phase the *declaration* skipped is stated, not left to the coverage number.

``run_integrity`` catches a phase that ran and delivered a placeholder (F5). It
cannot catch a phase the plan declined to run at all: the CSP solves once, from
the declaration, before Phase 1 dispatches, and a phase pinned ``S`` there leaves
no artefact, no stub and no trace.

Case 06 on 2026-09-11 is the reproduction. It is a composite system — a ranking
model beside a generative model — but the wizard cannot declare
``component_modalities``, so the solver saw one generative component, pinned
``P3`` and ``P4`` to ``S``, and the audit returned 57.1 % coverage with
``suitable_for_handoff: true`` and nothing anywhere saying model validation and
fairness had not been attempted. The reference run of the same case, whose Stage
A named both components, scored 100 %.

The rule this restores is the one fix 41 states one gate over: *silence is the
one answer worse than accept*. A high-risk system that never had its model or
its outputs examined must say so in the register the client reads, not only in a
percentage they have nothing to compare against.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.phases.compliance_matrix.logger import logger
from aaa.agents.tier1.phases.compliance_matrix.skipped_phases.plan import (
    _AT_STAKE,
    declaration_skipped_phases,
)
from aaa.tools.findings import make_finding

SKIPPED_PHASE_FINDING_ID = "ORCH-PHASE-SKIPPED-BY-DECLARATION"

def record_skipped_phases(state: dict) -> list[str]:
    """Raise one finding naming the phases the declaration skipped.

    :param state: The mutable AuditState dict.
    :returns: The phases reported, sorted.
    """
    findings: list[dict[str, Any]] = state.setdefault("blocking_findings", [])
    findings[:] = [f for f in findings if f.get("finding_id") != SKIPPED_PHASE_FINDING_ID]
    skipped = declaration_skipped_phases(state)
    if not skipped:
        return []

    articles = sorted({a for p in skipped for a in _AT_STAKE[p][1]})
    modalities = state.get("declared_modality") or "the declared modality"
    findings.append(make_finding(
        finding_id=SKIPPED_PHASE_FINDING_ID,
        description=(
            "This high-risk system was audited without "
            + " and without ".join(_AT_STAKE[p][0] for p in skipped)
            + f". The phase plan skipped {', '.join(skipped)} because the "
              f"declaration names a single {modalities} component and no "
              "component that ranks, scores or classifies. If any part of the "
              "system does so, those phases were skipped in error and the "
              "articles below are unevidenced as a result."),
        materiality="possibly_material",
        articles=articles,
        source_phase="ORCH",
        recommendation=(
            "Confirm whether the system has a ranking, scoring or classification "
            "component. If it does, declare it under component_modalities and "
            "re-run: the phase plan is solved from the declaration before any "
            "phase dispatches, so it cannot be corrected mid-run."),
        declared=modalities,
        observed=f"phase_plan: {', '.join(f'{p}=S' for p in skipped)}",
    ))
    logger.warning(
        "Phases %s skipped by declaration on a high-risk engagement; %s unevidenced.",
        ", ".join(skipped), ", ".join(articles))
    return skipped


__all__ = ["SKIPPED_PHASE_FINDING_ID", "declaration_skipped_phases",
           "record_skipped_phases"]
