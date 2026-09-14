"""Part 1 of the former ``csp_solver`` module (auto-split)."""
from __future__ import annotations

from typing import Dict, Iterable, Literal

from constraint import Problem

from aaa.tools.csp_solver.catalogue import merge_requirements

PhaseStatus = Literal["M", "O", "S"]


Plan = Dict[str, PhaseStatus]


def _pin(p: Problem, var: str, status: PhaseStatus) -> None:
    """Constrain one phase variable to a single status.

    :param p: The constraint problem being built.
    :param var: Phase variable name, e.g. ``"P4"``.
    :param status: The status the variable must take.
    """
    p.addConstraint(lambda x, _s=status: x == _s, [var])


def _apply_phase_catalogue(p: Problem, risk_tier: str | None,
                           modalities: Iterable[str],
                           is_llm_or_agentic: bool) -> None:
    """Encode the §6.2 phase-status catalogue as CSP constraints.

    For ``high`` the catalogue is applied per component modality and unioned,
    so a composite system carries every obligation any component attracts. The
    remaining tiers are scoped at system level and keep their scalar logic.

    :param p: The constraint problem being built.
    :param risk_tier: Verified (or declared) risk tier.
    :param modalities: Verified (or declared) modality of each AI component.
    :param is_llm_or_agentic: True when any component is generative.
    """
    if risk_tier == "high":
        for var, status in merge_requirements(modalities).items():
            _pin(p, var, status)
    elif risk_tier == "limited":
        if not is_llm_or_agentic:
            p.addConstraint(lambda p2, p5: p2 == "M" and p5 == "M", ["P2", "P5"])
            p.addConstraint(lambda p3, p4: p3 == "O" and p4 == "O", ["P3", "P4"])
        else:
            p.addConstraint(lambda p5, lb: p5 == "M" and lb == "M", ["P5", "L"])
            _pin(p, "P2", "O")
    elif risk_tier == "minimal":
        _pin(p, "P5", "M")
        _pin(p, "P2", "O")
        p.addConstraint(lambda p3, p4, cyber, priv: all(x == "S" for x in [p3, p4, cyber, priv]), ["P3", "P4", "CYBER", "PRIV"])
        _pin(p, "L", "O" if is_llm_or_agentic else "S")
    elif risk_tier == "gpai":
        p.addConstraint(lambda p5, lb, cyber: p5 == "M" and lb == "M" and cyber == "M", ["P5", "L", "CYBER"])
        _pin(p, "P2", "O")
