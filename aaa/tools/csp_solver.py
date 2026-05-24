from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Literal, Optional, Any
from constraint import Problem

if TYPE_CHECKING:
    from src.platform.state import AuditState

PhaseStatus = Literal["M", "O", "S"]
Plan = Dict[str, PhaseStatus]

def build_phase_csp(state: AuditState) -> Problem:
    """
    Builds a constraint satisfaction problem to determine phase statuses (M/O/S).
    Encoded from ARCHITECTURE.md §6.2.
    """
    p = Problem()
    variables = ["P1", "P2", "P3", "P4", "P5", "P6", "L", "CYBER", "PRIV"]
    p.addVariables(variables, ["M", "O", "S"])

    risk_tier = state.get("risk_tier", state.get("declared_risk_tier"))
    modality = state.get("modality", state.get("declared_modality"))
    is_llm_or_agentic = state.get("is_llm_or_agentic", modality in {"llm", "agentic", "gpai"})
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

    # 3. LLM / Agentic Routing (Hard Constraint 1)
    if is_llm_or_agentic:
        p.addConstraint(lambda l: l in ["M", "O"], ["L"])
        p.addConstraint(lambda p3, p4: p3 == "S" and p4 == "S", ["P3", "P4"])
    else:
        p.addConstraint(lambda l: l == "S", ["L"])

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
    # This is a bit complex as the table is a matrix. We can encode it as a set of constraints.
    
    # Example: High Risk + Tabular
    if risk_tier == "high":
        if modality == "tabular":
            p.addConstraint(lambda p2, p3, p4, p5: all(x == "M" for x in [p2, p3, p4, p5]), ["P2", "P3", "P4", "P5"])
        elif modality == "cv":
            p.addConstraint(lambda p2, p3, p4, p5, cyber: all(x == "M" for x in [p2, p3, p4, p5, cyber]), ["P2", "P3", "P4", "P5", "CYBER"])
        elif modality == "nlp":
            p.addConstraint(lambda p2, p3, p4, p5: all(x == "M" for x in [p2, p3, p4, p5]), ["P2", "P3", "P4", "P5"])
            p.addConstraint(lambda priv: priv == "M", ["PRIV"]) # PII
        elif modality == "time_series":
            p.addConstraint(lambda p2, p3, p5: all(x == "M" for x in [p2, p3, p5]), ["P2", "P3", "P5"])
            p.addConstraint(lambda p4: p4 == "O", ["P4"])
        elif modality in ["llm", "agentic"]:
            p.addConstraint(lambda p2, p5, l, cyber: all(x == "M" for x in [p2, p5, l, cyber]), ["P2", "P5", "L", "CYBER"])

    elif risk_tier == "limited":
        if not is_llm_or_agentic:
            p.addConstraint(lambda p2, p5: p2 == "M" and p5 == "M", ["P2", "P5"])
            p.addConstraint(lambda p3, p4: p3 == "O" and p4 == "O", ["P3", "P4"])
        else:
            p.addConstraint(lambda p5, l: p5 == "M" and l == "M", ["P5", "L"])
            p.addConstraint(lambda p2: p2 == "O", ["P2"])

    elif risk_tier == "minimal":
        p.addConstraint(lambda p5: p5 == "M", ["P5"])
        p.addConstraint(lambda p2: p2 == "O", ["P2"])
        p.addConstraint(lambda p3, p4, cyber, priv: all(x == "S" for x in [p3, p4, cyber, priv]), ["P3", "P4", "CYBER", "PRIV"])
        if is_llm_or_agentic:
            p.addConstraint(lambda l: l == "O", ["L"])
        else:
            p.addConstraint(lambda l: l == "S", ["L"])

    elif risk_tier == "gpai":
        p.addConstraint(lambda p5, l, cyber: p5 == "M" and l == "M" and cyber == "M", ["P5", "L", "CYBER"])
        p.addConstraint(lambda p2: p2 == "O", ["P2"])

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
