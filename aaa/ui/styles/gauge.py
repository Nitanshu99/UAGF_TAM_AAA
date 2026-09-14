"""SVG score-gauge for the conformity headline.

The arc draws itself from zero on every render: a `stroke-dashoffset` keyframe
whose start value is the full arc length, which is the one number the animation
needs and the one the caller already knows. Reduced motion turns the draw off
rather than shortening it, because a half-speed sweep is the jarring version.

The number is real text in the DOM, not generated content — it is the single
most meaningful thing on the results page and must reach assistive technology
(WCAG F87).
"""
from __future__ import annotations

import html

#: verdict → arc colour token. Kept as tokens so the gauge follows the palette.
_GAUGE_TOKENS = {"PASS": "var(--ok)", "PASS_WITH_OBSERVATIONS": "var(--warn)",
                 "FAIL": "var(--bad)"}
_ARC_LENGTH = 157.0  # length of the 180° arc path below (r = 50)


def score_gauge(score: float | None, label: str, verdict: str | None = None) -> str:
    """Return HTML for a semicircular 0–100 gauge.

    :param score: Value in [0, 100], or ``None`` when there is nothing to score
        (no article applies) — the gauge then draws the bare track with a dash
        and says so: no value arc, so nothing sits at zero.
    :type score: float | None
    :param label: Caption under the number, e.g. ``Article conformity``.
    :type label: str
    :param verdict: Final verdict — selects the arc colour (neutral when unknown).
    :type verdict: str | None
    :returns: Self-contained HTML/SVG markup.
    :rtype: str
    """
    caption = html.escape(label)
    if score is None:
        return _markup(f"{caption}: not applicable", "", None,
                       "—", f"{caption} · not applicable")
    score = max(0.0, min(100.0, score))
    color = _GAUGE_TOKENS.get((verdict or "").upper(), "var(--text-3)")
    return _markup(f"{caption}: {score:.0f} out of 100", color,
                   _ARC_LENGTH * score / 100.0, f"{score:.0f}", f"{caption} / 100")


def _markup(aria: str, color: str, filled: float | None, number: str, caption: str) -> str:
    """The gauge SVG around already-escaped text.

    With ``filled=None`` there is no value arc at all: a zero-length dash with a
    round linecap still paints a dot at the zero end, which reads as a score of 0.
    The caption sits below the track (whose round ends reach y = 65), so a long
    caption cannot run over them.
    """
    return (
        f'<div class="aaa-gauge" role="img" aria-label="{aria}">'
        '<svg viewBox="0 0 120 78">'
        '<path d="M 10 60 A 50 50 0 0 1 110 60" fill="none" stroke="var(--surface-3)"'
        ' stroke-width="10" stroke-linecap="round"/>'
        + ("" if filled is None else
           f'<path class="aaa-arc" d="M 10 60 A 50 50 0 0 1 110 60" fill="none" stroke="{color}"'
           f' stroke-width="10" stroke-linecap="round" style="--arc-len:{_ARC_LENGTH:.0f}"'
           f' stroke-dasharray="{filled:.1f} {_ARC_LENGTH:.0f}"/>')
        + f'<text x="60" y="52" text-anchor="middle" font-size="22" font-weight="700"'
        f' letter-spacing="-1" fill="var(--text)">{number}</text>'
        f'<text x="60" y="76" text-anchor="middle" font-size="7"'
        f' fill="var(--text-3)">{caption}</text>'
        "</svg></div>"
    )
