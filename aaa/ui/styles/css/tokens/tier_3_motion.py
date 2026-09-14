"""tier 3: motion — one ``:root`` block; multiple blocks cascade identically."""
from __future__ import annotations

TIER_3_MOTION = """
:root {
/* ---- tier 3: motion ---- */
  --ease: cubic-bezier(0.2, 0.7, 0.3, 1);
  --dur-1: 0.18s;
  --dur-2: 0.34s;
  --dur-3: 0.6s;
}
"""

__all__ = ["TIER_3_MOTION"]
