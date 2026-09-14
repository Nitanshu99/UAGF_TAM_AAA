"""Promote an optional phase to mandatory when the provider supplied the evidence it examines.

The §6.2 catalogue marks some phases ``O`` (optional) for lower tiers, and the
Orchestrator treats an optional phase as not owed, so it is never dispatched. When
the provider has uploaded the model and the data that phase tests, leaving it
unexamined disregards evidence in hand; an opinion must consider all relevant
evidence obtained, whether it corroborates or contradicts (ISA 330 ¶26). A phase
pinned ``S`` is a routing decision (no component of that kind) and is never promoted, except
Phases 3/4 of a minimal-risk system, examined voluntarily (Art. 95; user decision T-075).
"""
from __future__ import annotations

from typing import Any

DATASET = ("evaluation_dataset_uri", "training_dataset_uri")
MODEL = ("model_artifact_uri",)
GOLDEN_SET = ("golden_set_uri",)

# Phase variable → evidence groups that must all be supplied (any key within a group).
SUPPLIED_EVIDENCE: dict[str, tuple[tuple[str, ...], ...]] = {
    "P2": (DATASET,),
    "P3": (MODEL, DATASET),
    "P4": (MODEL, DATASET),
    "L": (GOLDEN_SET,),
}


def _dossier(state: dict[str, Any]) -> dict[str, Any]:
    """Return the Stage B dossier the phases will load their inputs from."""
    return (state.get("client_submission") or {}).get("stage_b") or {}


def _voluntary(state: dict[str, Any], phase: str, status: Any) -> bool:
    """A phase the minimal tier skipped for a discriminative component (user decision, T-075).

    The catalogue skips Phases 3/4 for a minimal-risk system because no requirement
    binds it, not because nothing is there to test. Evidence the provider supplied is
    then examined voluntarily (Art. 95 codes of conduct); the compliance matrix keeps
    only binding articles, so the results are observations, never verdicts. A skip for
    a generative-only or prohibited system is routing and is never opened.
    """
    from aaa.tools.csp_solver.catalogue import DISCRIMINATIVE, component_modalities

    return (status == "S" and phase in {"P3", "P4"}
            and state.get("risk_tier", state.get("declared_risk_tier")) == "minimal"
            and bool(set(component_modalities(state)) & DISCRIMINATIVE))


def promote_supplied(state: dict[str, Any], plan: dict[str, Any]) -> dict[str, str]:
    """Raise each optional — or voluntarily examinable — phase whose evidence was supplied to ``M``.

    :param state: The AuditState the plan was solved from.
    :param plan: Phase variable → status; promoted entries are rewritten.
    :returns: Phase variable → why it was promoted.
    """
    dossier = _dossier(state)
    reasons: dict[str, str] = {}
    for phase, groups in SUPPLIED_EVIDENCE.items():
        voluntary = _voluntary(state, phase, plan.get(phase))
        if plan.get(phase) != "O" and not voluntary:
            continue
        if not all(any(dossier.get(key) for key in group) for group in groups):
            continue
        plan[phase] = "M"
        supplied = ", ".join(key for group in groups for key in group if dossier.get(key))
        reasons[phase] = (
            f"not required for a minimal-risk system; examined voluntarily (Art. 95) because the "
            f"provider supplied {supplied} — findings are observations, not verdicts"
            if voluntary else
            f"optional under the catalogue, made mandatory because the provider supplied {supplied}")
    return reasons
