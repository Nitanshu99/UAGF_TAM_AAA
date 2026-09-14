"""Verdict and auditor-opinion pills.

Two vocabularies, deliberately kept apart:

* :func:`verdict_badge` prints the raw token (``PASS_WITH_OBSERVATIONS``). It
  is what the admin console and the audit trail speak, and what the
  disclaimer-of-opinion contract test pins.
* :func:`verdict_pill` prints what the customer is told (``Met, with
  observations``), reusing the client brief's vocabulary so the dashboard and
  the brief the customer downloads cannot describe the same verdict
  differently.
"""
from __future__ import annotations

import html

#: Verdict → the tone class it wears. Verdicts are information, so each keeps a
#: distinct hue *and* the label spells the state out (WCAG 1.4.1).
_VERDICT_TONE: dict[str, str] = {
    "PASS": "is-ok",
    "PASS_WITH_OBSERVATIONS": "is-warn",
    "FAIL": "is-bad",
    "DISCLAIMER_OF_OPINION": "is-none",
    "INSUFFICIENT_EVIDENCE": "is-none",
    "NOT_APPLICABLE": "is-info",
    "NOT_TESTED": "is-none",
    "PENDING": "is-none",
}

#: Verdicts the client-brief vocabulary has no wording for.
_EXTRA_LABELS = {
    "NOT_APPLICABLE": "Does not apply",
    "NOT_TESTED": "Not assessed",
    "PENDING": "In progress",
    "DISCLAIMER_OF_OPINION": "No opinion could be given",
}


def verdict_tone(verdict: str | None) -> str:
    """Return the pill tone class for *verdict*."""
    return _VERDICT_TONE.get((verdict or "PENDING").upper(), "is-none")


def verdict_badge(verdict: str | None) -> str:
    """Pill showing the raw verdict token, for technical surfaces.

    :param verdict: Verdict string; ``None`` renders as ``PENDING``.
    :returns: HTML ``<span>`` markup.
    """
    v = (verdict or "PENDING").upper()
    return f'<span class="aaa-pill {verdict_tone(v)}">{html.escape(v)}</span>'


def verdict_pill(verdict: str | None) -> str:
    """Pill showing the customer-facing wording for *verdict*.

    :param verdict: Verdict string; ``None`` renders as ``PENDING``.
    :returns: HTML ``<span>`` markup.
    """
    from aaa.agents.tier2.client_brief.constants import VERDICT_LABELS
    v = (verdict or "PENDING").upper()
    label = VERDICT_LABELS.get(v) or _EXTRA_LABELS.get(v) or v.replace("_", " ").capitalize()
    return f'<span class="aaa-pill {verdict_tone(v)}">{html.escape(label)}</span>'


def opinion_badge(opinion: str | None) -> str:
    """Pill for the auditor opinion type.

    :param opinion: ``adverse`` / ``disclaimer_of_opinion`` / ``qualified`` /
        ``unqualified``; ``None`` renders an em-dash.
    :returns: HTML ``<span>`` markup.
    """
    o = (opinion or "—").lower()
    tone = {"adverse": "is-bad", "disclaimer_of_opinion": "is-none",
            "qualified": "is-warn", "unqualified": "is-ok"}.get(o, "is-none")
    return f'<span class="aaa-pill {tone}">{html.escape(o.replace("_", " ").title())}</span>'
