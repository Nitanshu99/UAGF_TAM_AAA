"""Inject the auditor UI stylesheet once per page load.

Replaces the previous Bootstrap-over-CDN pass. Bootstrap gave the page a grid
and a badge class and, in exchange, a third-party network request on every load
and a visual identity that was recognisably somebody else's. Everything the app
actually used is now four hundred lines of first-party CSS built on two colour
tokens, which is both smaller and ours.
"""
from __future__ import annotations

import streamlit as st

from aaa.ui.styles.css import STYLESHEET


def inject_theme() -> None:
    """Load the stylesheet. Call once, near the top of ``main()``."""
    st.markdown(f"<style>{STYLESHEET}</style>", unsafe_allow_html=True)
