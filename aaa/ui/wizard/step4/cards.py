"""The card heading each deliverable is announced with, and the brief rendered as PDF."""
from __future__ import annotations

import html
import logging

import streamlit as st

logger = logging.getLogger(__name__)


def _brief_pdf(eid: str, markdown: str | None) -> bytes | None:
    """Render the plain-language brief to PDF, or ``None`` when it cannot be."""
    if markdown is None:
        return None
    try:
        from aaa.tools.report_render.pdf.brief import build_brief_pdf
        return build_brief_pdf(markdown, eid)
    except Exception as exc:  # noqa: BLE001 — the formal report is still deliverable
        logger.warning("Client brief PDF render failed for %s: %s", eid, exc)
        return None

def _heading(glyph: str, title: str, body: str) -> None:
    """The text half of a download card, rendered inside its container."""
    st.markdown(
        f'<div style="font-size:1.35rem;line-height:1" aria-hidden="true">{glyph}</div>'
        f'<div style="font-weight:620;margin-block:.55rem .2rem">{html.escape(title)}</div>'
        f'<p class="aaa-section-sub" style="font-size:.9rem;margin-block-end:1rem">'
        f"{html.escape(body)}</p>", unsafe_allow_html=True)


__all__ = ["_brief_pdf", "_heading"]
