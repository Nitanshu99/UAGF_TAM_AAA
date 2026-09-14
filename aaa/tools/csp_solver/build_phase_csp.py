"""Part 2 of the former ``csp_solver`` module (auto-split)."""
from __future__ import annotations

from typing import TYPE_CHECKING

from constraint import Problem

from aaa.tools.csp_solver.catalogue import DISCRIMINATIVE, GENERATIVE, component_modalities
from aaa.tools.csp_solver.phasestatus import PhaseStatus, Plan, _apply_phase_catalogue  # noqa: F401

if TYPE_CHECKING:
    from aaa.platform.state import AuditState


def build_phase_csp(state: AuditState) -> Problem:
    """
    Builds a constraint satisfaction problem to determine phase statuses (M/O/S).
    Encoded from ARCHITECTURE.md §6.2.
    """
    p = Problem()
    variables = ["P1", "P2", "P3", "P4", "P5", "P6", "L", "CYBER", "PRIV"]
    p.addVariables(variables, ["M", "O", "S"])

    risk_tier = state.get("risk_tier", state.get("declared_risk_tier"))
    modalities = component_modalities(state)
    has_discriminative = bool(set(modalities) & DISCRIMINATIVE)
    is_llm_or_agentic = state.get("is_llm_or_agentic",
                                  bool(set(modalities) & GENERATIVE))
    annex_iii_mapping = state.get("annex_iii_mapping", [])
    special_category_data = state.get("special_category_data", False)

    # 1. P1 and P6 are always Mandatory (P6 may be restricted if prohibited)
    p.addConstraint(lambda p1: p1 == "M", ["P1"])
    p.addConstraint(lambda p6: p6 == "M", ["P6"])

    # 2. Prohibited case
    if risk_tier == "prohibited":
        for v in ["P2", "P3", "P4", "P5", "L", "CYBER", "PRIV"]:
            p.addConstraint(lambda x: x == "S", [v])
        return p

    # 3. Component routing (Hard Constraint 1). The L-branch is added whenever a
    #    generative component is present; Phases 3 and 4 are skipped only when
    #    *no* component is discriminative. A composite system — an embedding
    #    ranking model plus a generative model, say — therefore keeps both, because the
    #    Act assesses conformity of the system (Art. 6, Annex IV §1), not of
    #    whichever component happens to set the modality field.
    if is_llm_or_agentic:
        p.addConstraint(lambda lb: lb in ["M", "O"], ["L"])
        if not has_discriminative:
            p.addConstraint(lambda p3, p4: p3 == "S" and p4 == "S", ["P3", "P4"])
    else:
        p.addConstraint(lambda lb: lb == "S", ["L"])

    # 4. Annex III Section 1 (Biometrics) (Hard Constraint 2)
    if any(e.get("annex_iii_section") == "1" for e in annex_iii_mapping):
        p.addConstraint(lambda cyber, priv: cyber == "M" and priv == "M", ["CYBER", "PRIV"])

    # 5. Special Category Data (Hard Constraint 3)
    if special_category_data:
        p.addConstraint(lambda priv: priv == "M", ["PRIV"])

    # 6. High Risk (Hard Constraint 4)
    if risk_tier == "high":
        p.addConstraint(lambda p5: p5 == "M", ["P5"])

    # 7. Apply Phase-Status Catalogue from §6.2
    _apply_phase_catalogue(p, risk_tier, modalities, is_llm_or_agentic)

    return p


def solve_phase_plan(state: AuditState) -> Plan:
    """
    Solves the CSP and returns a unique phase plan.
    If multiple solutions exist, returns the first one (most conservative).
    If no solution, raises a ValueError (to be handled by HITL).
    """
    p = build_phase_csp(state)
    solutions = p.getSolutions()

    if not solutions:
        raise ValueError("Over-constrained CSP: No valid phase plan found for this engagement.")

    # Sort solutions to prefer 'M' over 'O' over 'S' for a conservative approach
    status_score = {"M": 2, "O": 1, "S": 0}

    def score_solution(sol):
        return sum(status_score[v] for v in sol.values())

    best_solution = max(solutions, key=score_solution)
    return best_solution
