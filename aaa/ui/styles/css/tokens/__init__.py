"""Tier-1 and tier-2 design tokens for the auditor UI.

The palette is deliberately **two-tone**: everything on screen is either a
neutral derived from ``--ink`` (a deep navy) or the ``--brand`` indigo that
carries every action. Neutrals are mixed from the ink seed rather than taken
from a grey ramp, so surfaces, rules and muted text all share one hue and the
page reads as a single material.

Verdict colours are the one exception. They are *information*, not decoration —
WCAG 1.4.1 forbids carrying state in colour alone, and a compliance verdict is
the state the whole product exists to communicate — so PASS / FAIL / attention
keep distinct hues (and are always paired with a label and a glyph).
"""

# One ``:root`` block per tier — several blocks cascade exactly as one does,
# and the tiers are what a reader of the palette actually navigates by.
from __future__ import annotations

from aaa.ui.styles.css.tokens.browser_generated_ui import BROWSER_GENERATED_UI
from aaa.ui.styles.css.tokens.forced_colors import FORCED_COLORS
from aaa.ui.styles.css.tokens.tier_1_the_two_tones import TIER_1_THE_TWO_TONES
from aaa.ui.styles.css.tokens.tier_2_brand_derivatives import TIER_2_BRAND_DERIVATIVES
from aaa.ui.styles.css.tokens.tier_2_neutrals_all_mixed_from_the_ink_seed import (
    TIER_2_NEUTRALS_ALL_MIXED_FROM_THE_INK_SEED,
)
from aaa.ui.styles.css.tokens.tier_2_verdict_semantics import TIER_2_VERDICT_SEMANTICS
from aaa.ui.styles.css.tokens.tier_3_motion import TIER_3_MOTION
from aaa.ui.styles.css.tokens.tier_3_shape_depth_rhythm import TIER_3_SHAPE_DEPTH_RHYTHM

TOKENS = "".join((TIER_1_THE_TWO_TONES, TIER_2_NEUTRALS_ALL_MIXED_FROM_THE_INK_SEED, TIER_2_BRAND_DERIVATIVES, TIER_2_VERDICT_SEMANTICS, TIER_3_SHAPE_DEPTH_RHYTHM, TIER_3_MOTION, BROWSER_GENERATED_UI, FORCED_COLORS))

__all__ = ["TOKENS"]
