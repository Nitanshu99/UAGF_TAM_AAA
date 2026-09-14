"""tier 2: verdict semantics — one ``:root`` block; multiple blocks cascade identically."""
from __future__ import annotations

TIER_2_VERDICT_SEMANTICS = """
:root {
/* ---- tier 2: verdict semantics ---- */
  --ok: oklch(0.485 0.115 155);
  --warn: oklch(0.505 0.115 62);
  --bad: oklch(0.515 0.195 25);
  --none: var(--text-3);
  --ok-soft: color-mix(in oklab, var(--ok) 11%, white);
  --warn-soft: color-mix(in oklab, var(--warn) 13%, white);
  --bad-soft: color-mix(in oklab, var(--bad) 10%, white);
  --none-soft: var(--surface-3);
}
"""

__all__ = ["TIER_2_VERDICT_SEMANTICS"]
