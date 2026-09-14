"""The three "here is what happens" panels on the welcome screen."""
from __future__ import annotations

import html

import streamlit as st

#: (glyph, heading, body) — the whole engagement in three sentences, so nobody
#: has to guess what they are agreeing to before they upload anything.
_PANELS: tuple[tuple[str, str, str], ...] = (
    ("📄", "You share what you have",
     "Model cards, spec sheets, risk assessments, a dataset — whatever exists, "
     "plus a short form. Missing documents are a finding, not a blocker."),
    ("🤖", "We audit it, article by article",
     "Fourteen specialist agents check your system against every EU AI Act "
     "obligation that applies to it, and quote your documents as evidence."),
    ("📊", "You get a plain-language report",
     "One PDF written for you, not for a lawyer: what passed, what did not, and "
     "what to fix first."),
)


def render_panels() -> None:
    """Render the three-step explainer under the hero."""
    cards = "".join(
        f'<div class="aaa-card" style="--i:{i + 1}">'
        f'<div style="font-size:1.55rem;line-height:1" aria-hidden="true">{glyph}</div>'
        f'<div style="font-weight:620;margin-block:.7rem .3rem">{html.escape(head)}</div>'
        f'<div class="aaa-section-sub" style="font-size:.9rem">{html.escape(body)}</div>'
        "</div>"
        for i, (glyph, head, body) in enumerate(_PANELS))
    st.markdown(f'<div class="aaa-tiles aaa-tiles-2" style="margin-block-start:1.2rem">'
                f"{cards}</div>", unsafe_allow_html=True)
