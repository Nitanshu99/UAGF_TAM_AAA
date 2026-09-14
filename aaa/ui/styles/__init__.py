"""First-party design system for the auditor UI.

Two colour tones — a deep navy ``--ink`` and an indigo ``--brand`` — with every
neutral mixed from the ink seed, so the whole product reads as one material.
Verdict hues are the deliberate exception: a compliance state must never be
carried by colour alone *or* be indistinguishable from its neighbours.

Call :func:`inject_theme` once at the top of ``main()``; everything else here
returns or renders markup that the stylesheet already knows how to style.
"""
from __future__ import annotations

from aaa.ui.styles.badges import opinion_badge, verdict_badge, verdict_pill, verdict_tone
from aaa.ui.styles.components import compliance_table, kpi_cards, section_title, stat_tile
from aaa.ui.styles.findings import finding_row
from aaa.ui.styles.gauge import score_gauge
from aaa.ui.styles.hero import hero, note
from aaa.ui.styles.stepper import render_stepper
from aaa.ui.styles.theme import inject_theme

__all__ = [
    "inject_theme", "verdict_badge", "verdict_pill", "verdict_tone", "opinion_badge",
    "kpi_cards", "stat_tile", "compliance_table", "finding_row", "section_title",
    "score_gauge", "hero", "note", "render_stepper",
]
