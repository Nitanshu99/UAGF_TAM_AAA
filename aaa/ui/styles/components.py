"""KPI tiles, the article table, and section headings."""
from __future__ import annotations

import html

import streamlit as st

from aaa.ui.styles.badges import verdict_badge


def kpi_cards(kpis: list[tuple[str, str, str]]) -> None:
    """Render a row of KPI cards.

    :param kpis: Tuples of ``(label, value, band)``; empty band hides the chip.
    """
    cols = st.columns(len(kpis))
    for i, (col, (label, value, band)) in enumerate(zip(cols, kpis)):
        band_html = f'<div class="foot">{verdict_badge(band)}</div>' if band else ""
        col.markdown(
            f'<div class="aaa-kpi" style="--i:{i}"><div class="label">{html.escape(label)}</div>'
            f'<div class="value">{html.escape(value)}</div>{band_html}</div>',
            unsafe_allow_html=True,
        )


def stat_tile(label: str, value: str, unit: str = "", foot: str = "",
              meter: float | None = None, tone: str = "", index: int = 0) -> str:
    """Return the markup for one dashboard statistic.

    :param label: What is being counted.
    :param value: The number itself, already formatted.
    :param unit: Suffix rendered smaller than the value (``%``, ``/ 17``).
    :param foot: A short line under the number; may contain pre-escaped HTML.
    :param meter: ``0``–``1`` fill for the bar under the number; ``None`` hides it.
    :param tone: ``is-ok`` / ``is-warn`` / ``is-bad`` for the bar.
    :param index: Position in the row, used to stagger the entry animation.
    :returns: HTML markup for one tile.
    """
    unit_html = f'<span class="unit">{html.escape(unit)}</span>' if unit else ""
    meter_html = ("" if meter is None else
           f'<div class="aaa-meter" aria-hidden="true"><i class="{tone}" '
           f'style="inline-size:{max(0.0, min(1.0, meter)) * 100:.0f}%"></i></div>')
    return (f'<div class="aaa-kpi" style="--i:{index}">'
            f'<div class="label">{html.escape(label)}</div>'
            f'<div class="value">{html.escape(value)}{unit_html}</div>'
            f'{meter_html}{f"<div class=foot>{foot}</div>" if foot else ""}</div>')


def compliance_table(matrix: dict[str, str]) -> None:
    """Render the article → verdict matrix as a colour-coded table.

    :param matrix: Mapping of EU AI Act article to verdict string.
    """
    rows = "".join(
        f"<tr><td><code>{html.escape(article)}</code></td>"
        f"<td>{verdict_badge(verdict)}</td></tr>"
        for article, verdict in sorted(matrix.items())
    )
    st.markdown(
        '<div class="aaa-card aaa-scroll-x"><table class="aaa-matrix">'
        "<thead><tr><th>EU AI Act article</th><th>Verdict</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></div>",
        unsafe_allow_html=True,
    )


def section_title(title: str, subtitle: str = "") -> None:
    """Render a styled section heading.

    :param title: Heading text.
    :param subtitle: Optional muted sub-heading.
    """
    sub = f'<div class="aaa-section-sub">{html.escape(subtitle)}</div>' if subtitle else ""
    st.markdown(
        f'<div style="margin-block:1.9rem .8rem">'
        f'<h2 class="aaa-section-title">{html.escape(title)}</h2>{sub}</div>',
        unsafe_allow_html=True,
    )
