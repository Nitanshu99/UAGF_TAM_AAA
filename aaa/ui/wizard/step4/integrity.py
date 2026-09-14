"""Degraded-run banner for the results page — fix F5 (finding S3).

The results page renders a verdict, a conformity gauge and four KPI cards
whether or not the phases behind them ran. On 2026-09-03 it would have shown
``DISCLAIMER_OF_OPINION`` over a 26.7 % coverage gauge for an engagement whose
Phase 1, Phase 5 and Phase 6 had all delivered placeholders — every number on
the page computed over artefacts that point at nothing, and nothing on the page
saying so.

This banner renders above the verdict for that reason: a reader who has already
formed an impression of the result is a reader who will carry it past whatever
caveat appears later. It states the count, names the phases, and says plainly
that the run is not deliverable — which is the sentence the human at the wizard
needs before they decide whether to send anything to a client.
"""
from __future__ import annotations

import streamlit as st

from aaa.platform.state.run_integrity import build_run_integrity

#: Phase id → the name a non-engineer reading the results page will recognise.
_PHASE_LABELS = {
    "INTAKE": "Intake", "P1": "Phase 1 Scope", "P2": "Phase 2 Data governance",
    "P3": "Phase 3 Model validation", "P4": "Phase 4 Output fairness",
    "P5": "Phase 5 Governance", "P6": "Phase 6 Reporting",
    "L": "L-branch", "CYBER": "Cybersecurity", "PRIV": "Privacy",
}


def phase_labels(integrity: dict) -> str:
    """Render *integrity*'s degraded phases as a human-readable list.

    :param integrity: A ``run_integrity`` block.
    :returns: Comma-separated phase names, e.g. ``"Phase 1 Scope, Phase 5 Governance"``.
    """
    return ", ".join(str(_PHASE_LABELS.get(p) or p) for p in integrity["degraded_phases"])


def render_integrity_banner(final: dict) -> dict:
    """Warn, above the verdict, when this run delivered placeholder artefacts.

    :param final: Final ``AuditState`` dictionary.
    :returns: The ``run_integrity`` block, so the caller can gate on it without
        recomputing.
    """
    integrity = final.get("run_integrity") or build_run_integrity(final)
    if integrity["suitable_for_handoff"]:
        return integrity
    stubs, total = len(integrity["stub_artefact_ids"]), integrity["artefact_count"]
    unwired = integrity["unwired_agents"]
    st.error(
        f"**This run is degraded and must not be handed to a client.**\n\n"
        f"{stubs} of {total} artefacts are placeholders, so "
        f"**{phase_labels(integrity)}** delivered no evidence. The verdict, the "
        f"conformity score and the findings below are computed over artefacts "
        f"whose URIs resolve to nothing."
        + (f"\n\nAgents that failed to start: `{'`, `'.join(unwired)}`."
           if unwired else "")
        + "\n\nRe-run the engagement once the cause is fixed."
    )
    with st.expander(f"Which {stubs} artefacts are placeholders?", expanded=False):
        st.write("\n".join(f"- `{tid}`" for tid in integrity["stub_artefact_ids"]))
    return integrity


__all__ = ["render_integrity_banner", "phase_labels"]
