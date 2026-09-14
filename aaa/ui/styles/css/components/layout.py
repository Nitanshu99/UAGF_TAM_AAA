"""The layout surface."""
from __future__ import annotations

LAYOUT = """
/* Rows of equal-height cards. Authored as one grid rather than as Streamlit
   columns, because a Streamlit column does not pass its height down to the
   markdown container inside it — so `block-size: 100%` on a card there resolves
   against nothing and every tile ends up only as tall as its own text. */
.aaa-tiles { display: grid; gap: 0.9rem;
  grid-template-columns: repeat(auto-fit, minmax(13.5rem, 1fr)); }
.aaa-tiles-2 { grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr)); }
.aaa-split { display: grid; gap: 1rem; align-items: stretch;
  grid-template-columns: minmax(0, 2.5fr) minmax(14rem, 1fr); }
@media (width < 60rem) { .aaa-split { grid-template-columns: 1fr; } }

/* Where a row genuinely needs Streamlit widgets in it, opt that row into
   stretching by marking one of its children. */
[data-testid="stHorizontalBlock"]:has(.aaa-equal) [data-testid="stColumn"] > div,
[data-testid="stHorizontalBlock"]:has(.aaa-equal) [data-testid="stColumn"]
  > div > [data-testid="stVerticalBlock"] { block-size: 100%; }

.aaa-gauge { inline-size: 100%; display: grid; justify-items: center; }
.aaa-gauge svg { inline-size: min(15rem, 100%); aspect-ratio: 120 / 78;
  display: block; overflow: visible; }
"""

__all__ = ["LAYOUT"]
