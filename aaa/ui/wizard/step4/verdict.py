"""The dashboard masthead: whose system, what we concluded, in what words."""
from __future__ import annotations

import html
from datetime import datetime, timezone

import streamlit as st

from aaa.ui.styles import score_gauge
from aaa.ui.wizard.step4.header import article_score, verdict_words

#: what the gauge measures, and what it says when there is nothing to measure
_GAUGE_NOTE = "How much of what applies to you is already met."
_NOTHING_APPLIES = ("No EU AI Act requirement applies at your system's risk tier, "
                    "so there is nothing to score.")


def completed_on(final: dict) -> str | None:
    """When the audit's final state was saved, in UTC — never the time of viewing.

    The chip was ``datetime.now()`` at render, so it dated the audit by whenever
    the page was opened (T-20260914-003).

    :param final: Final ``AuditState`` dictionary.
    :returns: ``Completed 13 September 2026, 22:29 UTC``, or ``None`` when unrecorded.
    """
    stamp = (final.get("run_integrity") or {}).get("generated_at")
    try:
        when = datetime.fromisoformat(str(stamp)).astimezone(timezone.utc)
    except ValueError:
        return None
    return when.strftime("Completed %d %B %Y, %H:%M UTC")


def _chips(eid: str, final: dict) -> list[str]:
    """Facts the customer may need to quote back to us."""
    annex = ", ".join(f"§{s}" for s in final.get("declared_annex_iii_sections") or [])
    chips = [f"Reference {eid}", *[c for c in [completed_on(final)] if c],
             f"{(final.get('risk_tier') or 'unspecified').title()}-risk system"]
    if annex:
        chips.append(f"Annex III {annex}")
    return chips


def render_verdict(eid: str, final: dict) -> None:
    """Render the masthead: system identity, the conclusion, and the score.

    :param eid: Engagement identifier.
    :param final: Final ``AuditState`` dictionary.
    """
    stage_a = (final.get("client_submission") or {}).get("stage_a") or {}
    system = f"{stage_a.get('system_name', '')} {stage_a.get('version', '')}".strip()
    headline, meaning = verdict_words(final.get("final_verdict"))
    chips = "".join(f'<span class="aaa-hero-chip">{html.escape(c)}</span>'
                    for c in _chips(eid, final))
    score = article_score(final.get("compliance_matrix") or {})
    st.markdown(
        f'<div class="aaa-split">'
        f'<header class="aaa-hero aaa-rise">'
        f'<div class="aaa-eyebrow">{html.escape(stage_a.get("provider_name") or "")}'
        f'{" · " + html.escape(system) if system else ""}</div>'
        f'<h1 class="aaa-hero-title">{html.escape(headline)}</h1>'
        f'<p class="aaa-hero-sub">{html.escape(meaning)}</p>'
        f'<div class="aaa-hero-meta">{chips}</div></header>'
        f'<aside class="aaa-card aaa-rise" style="--i:1;display:grid;'
        f'align-content:center;gap:.5rem">'
        f'{score_gauge(score, "Conformity", final.get("final_verdict"))}'
        f'<p class="aaa-muted" style="text-align:center;margin:0">'
        f"{_GAUGE_NOTE if score is not None else _NOTHING_APPLIES}</p></aside></div>",
        unsafe_allow_html=True)
