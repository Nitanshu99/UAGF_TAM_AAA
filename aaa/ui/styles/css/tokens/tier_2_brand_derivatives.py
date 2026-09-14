"""tier 2: brand derivatives — one ``:root`` block; multiple blocks cascade identically."""
from __future__ import annotations

TIER_2_BRAND_DERIVATIVES = """
:root {
/* ---- tier 2: brand derivatives ---- */
  --brand-hover: oklch(0.48 0.185 272);
  --brand-soft: color-mix(in oklab, var(--brand) 9%, white);
  --brand-line: color-mix(in oklab, var(--brand) 26%, white);
}
"""

__all__ = ["TIER_2_BRAND_DERIVATIVES"]
