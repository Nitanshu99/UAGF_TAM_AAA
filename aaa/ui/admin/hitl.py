"""The deferred-HITL review packet and the command that closes it."""
from __future__ import annotations

import json

import streamlit as st

from aaa.ui.styles import note, section_title


def render_hitl_panel(eid: str, final: dict) -> None:
    """Render the review packet when a qualified auditor's sign-off is pending.

    :param eid: Engagement identifier.
    :param final: Final ``AuditState`` dictionary.
    """
    if not final.get("hitl_required"):
        note("ok", "✓", "No human sign-off outstanding",
             "The Verifier did not escalate on this run, so the verdict the "
             "client sees is final.")
        return
    from aaa.tools.hitl_review import build_hitl_review_packet
    packet = build_hitl_review_packet(final)
    cases = packet.get("cases", [])
    section_title(f"Human review required — {len(cases)} case(s)",
                  packet.get("hitl_reason")
                  or "Some artefacts need a qualified auditor's sign-off.")
    st.code(
        f"# 1. download the packet below\n"
        f"# 2. set each case's human_decision: accept | uphold_escalation | override\n"
        f"python -m scripts.finalize_hitl {eid}", language="bash")
    st.download_button(
        "⬇ HITL review packet (JSON)",
        data=json.dumps(packet, indent=2, default=str).encode(),
        file_name=f"{eid}_hitl_review.json", mime="application/json", type="primary")
    with st.expander("Inspect the packet", expanded=False):
        st.json(packet)
