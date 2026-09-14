"""The dashboard's top bar: the way in to the admin console, and the way out."""
from __future__ import annotations

import html

import streamlit as st

_ADMIN_CSS = """
<style>
/* The admin door is deliberately quiet: it belongs to us, not to the customer
   whose result this page is, so it reads as a utility rather than an action. */
.aaa-adminbar + [data-testid="stHorizontalBlock"] .stButton button {
  border-radius: var(--r-pill);
  background: transparent;
  border-color: var(--line);
  color: var(--text-3);
  box-shadow: none;
  min-block-size: 2.1rem;
  font-size: .82rem;
  padding-inline: .85rem;
}
.aaa-adminbar + [data-testid="stHorizontalBlock"] .stButton button:hover:not(:disabled) {
  color: var(--brand-hover);
  border-color: var(--brand-line);
  background: var(--brand-soft);
}
/* The reference sits opposite the button on a wide screen and underneath it on
   a narrow one, where right-aligned text would crowd the masthead below. */
.aaa-topref { margin: 0; padding-block-start: .55rem; text-align: end;
  overflow-wrap: anywhere; }
@media (width < 40rem) { .aaa-topref { text-align: start; padding-block-start: 0; } }
</style>
"""


def render_topbar(eid: str) -> None:
    """Render the admin entry point and the engagement reference.

    :param eid: Engagement identifier, shown so the customer can quote it.
    """
    st.markdown(_ADMIN_CSS + '<div class="aaa-adminbar"></div>', unsafe_allow_html=True)
    left, right = st.columns([1, 2])
    with left:
        if st.button("⚙  Admin console", key="open_admin",
                     help="Auditor tools: review packets, raw artefacts, run integrity."):
            st.session_state["view"] = "admin"
            st.rerun()
    right.markdown(
        f'<p class="aaa-muted aaa-topref">Engagement {html.escape(eid)}</p>',
        unsafe_allow_html=True)
