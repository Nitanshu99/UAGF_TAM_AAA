"""How a pending sign-off or a broken run is put to the customer.

The old page answered "human review required" by printing the HITL review
packet — a JSON object with a ``cases`` array — and telling the reader to run
``python -m scripts.finalize_hitl <id>``. That instruction is addressed to us.
The customer's question is only ever "is this final, and do I need to do
anything", so that is the question these two notes answer. The packet itself,
and the command, moved to the admin console.
"""
from __future__ import annotations

import streamlit as st

from aaa.ui.styles import note


def degraded_reason(integrity: dict) -> str:
    """Say what actually degraded the run, in the customer's terms.

    Three things bar a hand-off (``run_integrity``), and they are not the same
    sentence: a phase that never ran, a section written without its model, and
    evidence nobody independently checked. The Mariposa run of 2026-09-12 had
    only the second — one model call lost to an overloaded provider — and was
    told that "parts of the assessment did not run".

    :param integrity: The run's ``run_integrity`` block.
    :returns: One or more sentences naming each cause that applies.
    """
    causes: list[str] = []
    if integrity.get("stub_artefact_ids") or integrity.get("degraded_phases"):
        causes.append("Parts of the assessment did not run")
    if integrity.get("fallback_authored_phases"):
        causes.append("Some sections were assembled from the automated checks "
                      "alone because the model behind them was unavailable")
    if integrity.get("fallback_critique_ids"):
        causes.append("Some evidence was not independently verified")
    return (". ".join(causes) or "Parts of the assessment did not complete") + ", "


def render_status(final: dict, integrity: dict) -> bool:
    """Render the run's standing, in the customer's terms.

    :param final: Final ``AuditState`` dictionary.
    :param integrity: The run's ``run_integrity`` block.
    :returns: ``True`` when the run is degraded and must not be handed over.
    """
    degraded = not integrity["suitable_for_handoff"]
    if degraded:
        note("bad", "⚠",
             "This audit did not finish cleanly",
             degraded_reason(integrity)
             + "so the result below is incomplete and we are not releasing the "
             "report from it. Our team has been notified and will re-run your "
             "audit — you do not need to re-submit anything.")
        return True
    if final.get("hitl_required"):
        note("info", "◷",
             "Provisional — with a senior auditor for sign-off",
             "Everything below is our assessment, and it rarely changes at this "
             "stage. A qualified auditor reviews the points the system flagged "
             "before your report is final. Nothing is needed from you.")
    return False


def render_opinion(final: dict) -> None:
    """Render the auditor's own words about the conclusion, when there are any.

    :param final: Final ``AuditState`` dictionary.
    """
    opinion = (final.get("auditor_opinion") or {}).get("opinion_paragraph")
    if not opinion:
        return
    st.markdown(
        '<blockquote class="aaa-rise" style="border:0;border-inline-start:4px solid '
        'var(--brand);background:var(--brand-soft);border-start-end-radius:var(--r-lg);'
        'border-end-end-radius:var(--r-lg);margin:1.7rem 0 0;padding:1.1rem 1.3rem;'
        'font-size:1.02rem;line-height:1.65;color:var(--text);text-wrap:pretty">'
        f'<div class="aaa-eyebrow" style="margin-block-end:.45rem">The auditor\'s opinion</div>'
        f"{opinion}</blockquote>", unsafe_allow_html=True)
