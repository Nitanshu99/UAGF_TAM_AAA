"""Live completeness meter and scope-gate verdict for wizard step 3.

Two facts sit above the form and the customer needs both before they touch it:
how far off the 80 % gate they are, and whether their system is in scope at all.
They used to be a bare ``st.metric`` beside a raw ``st.progress`` and an alert
reading "⚠ Scope gate: out_of_scope" — three widgets, one of which printed an
internal enum. They are now one card that answers both questions in words.
"""
from __future__ import annotations

import html

import streamlit as st

from aaa.tools.scope_gate import scope_gate
from aaa.ui.wizard.live_view import live_report

#: gate verdict → (pill tone, glyph, the sentence a customer can act on).
_GATE_WORDS: dict[str, tuple[str, str, str]] = {
    "prohibited": ("is-bad", "✕", "This use is prohibited under the EU AI Act"),
    "excluded": ("is-warn", "!", "This may sit outside the Act"),
    "out_of_scope": ("is-warn", "!", "This may sit outside the Act"),
}
_IN_SCOPE = ("is-ok", "✓", "Your system is in scope — good to continue")


def _gate_block(gate) -> str:
    """Render the scope verdict and, when it is not clean, the reason."""
    tone, glyph, headline = _GATE_WORDS.get(gate.verdict, _IN_SCOPE)
    reason = (f'<p class="aaa-section-sub" style="font-size:.86rem;margin:.45rem 0 0">'
              f"{html.escape(gate.reasoning[0])}</p>"
              if gate.verdict in _GATE_WORDS and gate.reasoning else "")
    return (f'<div><div class="aaa-eyebrow">Scope</div>'
            f'<div style="margin-block-start:.4rem">'
            f'<span class="aaa-pill has-glyph {tone}">'
            f"{glyph} {html.escape(headline)}</span></div>{reason}</div>")


def _score_block(score: float | None) -> str:
    """Render the completeness figure against the gate it has to clear."""
    if score is None:
        return '<div><div class="aaa-eyebrow">Completeness</div></div>'
    tone = "is-ok" if score >= 0.80 else "is-warn"
    remaining = ("Ready to run." if score >= 0.80
                 else f"{(0.80 - score) * 100:.0f} points to go before the audit can start.")
    return (f'<div><div class="aaa-eyebrow">How complete this is</div>'
            f'<div class="value" style="font-size:2rem;font-weight:660;'
            f'letter-spacing:-.03em;line-height:1.1">{score:.0%}'
            f'<span class="unit" style="font-size:.5em;font-weight:560;'
            f'color:var(--text-3)"> of 80% needed</span></div>'
            f'<div class="aaa-meter" aria-hidden="true"><i class="{tone}" '
            f'style="inline-size:{min(score / 0.80, 1.0) * 100:.0f}%"></i></div>'
            f'<p class="aaa-section-sub" style="font-size:.86rem;margin:.45rem 0 0">'
            f"{html.escape(remaining)}</p></div>")


def render_score_and_gate(stage_a: dict, stage_b: dict):
    """Show the live completeness meter and the scope-gate verdict.

    :param stage_a: Current Stage A payload.
    :param stage_b: Current Stage B payload.
    :returns: ``(score, gate, report)`` — the navigation controls gate on the
        first two, the checklist reads the third.
    """
    report = live_report(stage_a, stage_b)
    score = None if report is None else float(report.score)
    gate = scope_gate(stage_a)
    st.markdown(
        '<div class="aaa-card aaa-rise" style="display:grid;gap:1.4rem;'
        'grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));'
        'margin-block:1rem 1.6rem">'
        f"{_score_block(score)}{_gate_block(gate)}</div>", unsafe_allow_html=True)
    return score, gate, report
