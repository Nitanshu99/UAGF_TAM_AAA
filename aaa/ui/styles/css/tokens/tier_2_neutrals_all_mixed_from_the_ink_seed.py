"""tier 2: neutrals, all mixed from the ink seed — one ``:root`` block; multiple blocks cascade identically."""
from __future__ import annotations

TIER_2_NEUTRALS_ALL_MIXED_FROM_THE_INK_SEED = """
:root {
/* ---- tier 2: neutrals, all mixed from the ink seed ---- */
  --canvas: oklch(0.985 0.004 268);
  --surface: #fff;
  --surface-2: oklch(0.972 0.006 268);
  --surface-3: oklch(0.952 0.010 268);
  --line: oklch(0.905 0.012 268);
  --line-strong: oklch(0.83 0.018 268);
  /* Interactive boundaries need 3:1 against their background
     (WCAG 1.4.11); --line-strong is a decorative edge and does not. */
  --control-line: oklch(0.635 0.026 268);
  --text: var(--ink);
  --text-2: oklch(0.455 0.028 268);
  --text-3: oklch(0.535 0.024 268);
  --on-ink: oklch(0.97 0.008 268);
}
"""

__all__ = ["TIER_2_NEUTRALS_ALL_MIXED_FROM_THE_INK_SEED"]
