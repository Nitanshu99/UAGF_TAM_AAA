"""Per-modality phase requirements for the §6.2 catalogue.

Split out of ``phasestatus`` so a *composite* system — one carrying more than
one AI component, e.g. a ranking model plus a generative model — can have the
catalogue applied once per component and the results unioned.

Before this module the catalogue was keyed on a single scalar modality, so a
generative component silently cancelled the discriminative phases: an Annex III
employment system whose *ranker* is the consequential component had its output
fairness assessment skipped because it also happened to contain an LLM.
"""
from __future__ import annotations

from typing import Dict, Iterable, Literal, Mapping

from aaa.platform.state.stage_a_lookup import stage_a_field

PhaseStatus = Literal["M", "O", "S"]

#: Ordering used when merging two components' requirements: the stronger wins.
RANK: Dict[str, int] = {"S": 0, "O": 1, "M": 2}

#: Modalities whose obligations are discharged by Phases 3 and 4.
DISCRIMINATIVE: frozenset[str] = frozenset({"tabular", "cv", "nlp", "time_series"})

#: Modalities routed to the UAGF-TAM-L branch.
GENERATIVE: frozenset[str] = frozenset({"llm", "agentic", "gpai"})

#: risk_tier ``high`` × modality → required phase statuses for that component.
HIGH_CATALOGUE: Dict[str, Dict[str, PhaseStatus]] = {
    "tabular": {"P2": "M", "P3": "M", "P4": "M", "P5": "M"},
    "cv": {"P2": "M", "P3": "M", "P4": "M", "P5": "M", "CYBER": "M"},
    "nlp": {"P2": "M", "P3": "M", "P4": "M", "P5": "M", "PRIV": "M"},
    "time_series": {"P2": "M", "P3": "M", "P5": "M", "P4": "O"},
    "llm": {"P2": "M", "P5": "M", "L": "M", "CYBER": "M"},
    "agentic": {"P2": "M", "P5": "M", "L": "M", "CYBER": "M"},
}


def merge_requirements(modalities: Iterable[str]) -> Dict[str, PhaseStatus]:
    """Union the high-risk catalogue across a system's component modalities.

    Where two components disagree on a phase the stronger status wins, so a
    composite system inherits every obligation either component carries.

    :param modalities: Declared modality of each AI component in the system.
    :returns: Phase variable → required status.
    :rtype: Dict[str, PhaseStatus]
    """
    merged: Dict[str, PhaseStatus] = {}
    for modality in modalities:
        for var, status in HIGH_CATALOGUE.get(modality, {}).items():
            if RANK[status] > RANK[merged.get(var, "S")]:
                merged[var] = status
    return merged


def component_modalities(state: Mapping[str, object]) -> list[str]:
    """Modality of each declared AI component, newest contract first.

    Falls back to the single scalar ``modality`` when a dossier predates the
    component contract, so legacy engagements route exactly as before.

    :param state: Audit state carrying the Stage A declaration.
    :returns: One modality string per AI component.
    :rtype: list[str]
    """
    declared = stage_a_field(state, "component_modalities")
    declared = declared or []
    if isinstance(declared, list):
        mods = [c.get("modality") for c in declared
                if isinstance(c, dict) and c.get("modality")]
        if mods:
            return [str(m) for m in mods]
    single = state.get("modality") or state.get("declared_modality")
    return [str(single)] if single else []


def discriminative_modality(state: Mapping[str, object]) -> str:
    """The modality Phases 3 and 4 assess: that of the first discriminative component.

    The planner already schedules P3 and P4 for a composite system's
    discriminative component, but the runners dispatched the scalar system
    modality. For case 06 that is ``llm``, so output fairness took the
    generative short-circuit and loaded nothing, and T11/T12/T13 recorded
    ``modality: llm`` for a ranking system (T-20260913-010). A system with no
    discriminative component keeps its scalar modality and routes as before.

    :param state: Audit state carrying the Stage A declaration.
    :returns: The first declared component modality in :data:`DISCRIMINATIVE`,
        else the scalar modality, else ``""``.
    """
    for modality in component_modalities(state):
        if modality.lower() in DISCRIMINATIVE:
            return modality.lower()
    single = state.get("modality") or state.get("declared_modality")
    return str(single) if single else ""
