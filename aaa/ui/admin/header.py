"""Admin masthead and the way back to the customer's dashboard."""
from __future__ import annotations

import html

import streamlit as st

_ADMIN_CSS = """
<style>
/* Admin is visibly a different room: the masthead is ink rather than indigo,
   so nobody mistakes an internal screen for something a client is looking at. */
.aaa-admin-bar { display: flex; align-items: center; justify-content: space-between;
  gap: 1rem; flex-wrap: wrap; background: var(--ink); color: var(--on-ink);
  border-radius: var(--r-lg); padding: .9rem 1.2rem; margin-block-end: 1.4rem; }
.aaa-admin-bar .who { font-weight: 640; letter-spacing: -.01em; }
.aaa-admin-bar .ref { font-size: .82rem;
  color: color-mix(in oklab, var(--on-ink) 72%, transparent); }
</style>
"""


def render_admin_header(eid: str, final: dict | None) -> None:
    """Render the admin bar and the back button.

    :param eid: Engagement identifier.
    :param final: Final ``AuditState``, or ``None`` when no run is loaded.
    """
    verdict = (final or {}).get("final_verdict") or "no run"
    st.markdown(
        _ADMIN_CSS
        + '<div class="aaa-admin-bar aaa-rise"><div>'
        '<div class="aaa-eyebrow" style="color:var(--brand-line)">Auditor console</div>'
        f'<div class="who">Internal review — not client-facing</div></div>'
        f'<div class="ref">{html.escape(eid)} · {html.escape(str(verdict))}</div></div>',
        unsafe_allow_html=True)
    if st.button("←  Back to the client dashboard", key="close_admin"):
        st.session_state["view"] = "customer"
        st.rerun()
