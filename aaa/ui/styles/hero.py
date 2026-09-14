"""Dark masthead used to open the welcome screen and the results dashboard."""
from __future__ import annotations

import html

import streamlit as st


def hero(eyebrow: str, title: str, subtitle: str = "", chips: list[str] | None = None) -> None:
    """Render the page masthead.

    :param eyebrow: Small upper-case kicker above the title.
    :param title: The page's headline.
    :param subtitle: One or two sentences of orientation.
    :param chips: Short facts shown as chips under the subtitle.
    """
    sub = (f'<p class="aaa-hero-sub">{html.escape(subtitle)}</p>' if subtitle else "")
    meta = "".join(f'<span class="aaa-hero-chip">{html.escape(c)}</span>' for c in chips or [])
    st.markdown(
        f'<header class="aaa-hero aaa-rise">'
        f'<div class="aaa-eyebrow">{html.escape(eyebrow)}</div>'
        f'<h1 class="aaa-hero-title">{html.escape(title)}</h1>{sub}'
        + (f'<div class="aaa-hero-meta">{meta}</div>' if meta else "")
        + "</header>",
        unsafe_allow_html=True)


def note(kind: str, glyph: str, title: str, text: str) -> None:
    """Render a bordered callout.

    Colour never carries the meaning alone — every callout has a glyph and a
    title that state the same thing in words (WCAG 1.4.1).

    :param kind: ``info`` / ``ok`` / ``warn`` / ``bad``.
    :param glyph: A short symbol shown before the title.
    :param title: The one-line statement.
    :param text: Supporting sentence(s); may contain pre-escaped HTML.
    """
    st.markdown(
        f'<div class="aaa-note is-{html.escape(kind)} aaa-rise">'
        f'<span class="glyph" aria-hidden="true">{html.escape(glyph)}</span>'
        f'<div><div class="title">{html.escape(title)}</div>'
        f'<div class="text">{text}</div></div></div>',
        unsafe_allow_html=True)
