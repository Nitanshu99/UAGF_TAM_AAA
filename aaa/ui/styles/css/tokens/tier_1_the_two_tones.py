"""tier 1: the two tones — one ``:root`` block; multiple blocks cascade identically."""
from __future__ import annotations

TIER_1_THE_TWO_TONES = """

:root {
  color-scheme: light;


/* ---- tier 1: the two tones ---- */
  --ink: oklch(0.24 0.045 268);
  --brand: oklch(0.55 0.185 272);
}
"""

__all__ = ["TIER_1_THE_TWO_TONES"]
