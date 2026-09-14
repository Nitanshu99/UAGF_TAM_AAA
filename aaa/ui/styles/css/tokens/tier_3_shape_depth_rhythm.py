"""tier 3: shape, depth, rhythm — one ``:root`` block; multiple blocks cascade identically."""
from __future__ import annotations

TIER_3_SHAPE_DEPTH_RHYTHM = """
:root {
/* ---- tier 3: shape, depth, rhythm ---- */
  --r-sm: 0.5rem;
  --r-md: 0.75rem;
  --r-lg: 1rem;
  --r-xl: 1.5rem;
  --r-pill: 999px;
  --shadow-1: 0 1px 2px oklch(0.24 0.045 268 / 0.05),
              0 1px 3px oklch(0.24 0.045 268 / 0.04);
  --shadow-2: 0 1px 2px oklch(0.24 0.045 268 / 0.05),
              0 10px 28px -8px oklch(0.24 0.045 268 / 0.14);
  --shadow-brand: 0 6px 20px -6px color-mix(in oklab, var(--brand) 45%, transparent);
  --measure: 68ch;
}
"""

__all__ = ["TIER_3_SHAPE_DEPTH_RHYTHM"]
