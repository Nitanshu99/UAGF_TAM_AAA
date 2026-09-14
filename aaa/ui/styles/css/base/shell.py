"""Shell — part of the base cascade layer."""
from __future__ import annotations

SHELL = """
/* ---- shell ------------------------------------------------------------ */
.stApp { background: var(--canvas); }
/* Streamlit's header is a transparent 60px band pinned at z-index 999990, and
   it sits *outside* `stMain` — the only element on the page that scrolls, since
   `stAppViewContainer` is `overflow: hidden`. A wheel anywhere in that strip is
   therefore swallowed: the customer sees their own content through it, scrolls,
   and nothing moves. Nothing in that band is even visible here — the rule below
   hides the toolbar, the menu and the status widget — so it is an empty overlay
   that only ever intercepts. `pointer-events: none` lets the wheel through; the
   toolbar takes its clicks back should it ever be shown again.

   `height: 0` is kept but does not win: measured live, the band is still 60px
   even with the `.stApp` prefix, because Streamlit sizes it more specifically
   still. That is why the fix is `pointer-events`, not geometry — the strip
   stays, and simply stops intercepting. */
.stApp [data-testid="stHeader"] {
  background: transparent;
  height: 0;
  pointer-events: none;
}
.stApp [data-testid="stHeader"] [data-testid="stToolbar"] { pointer-events: auto; }
[data-testid="stToolbar"], [data-testid="stAppDeployButton"],
[data-testid="stMainMenu"], [data-testid="stStatusWidget"], footer { display: none; }
[data-testid="stDecoration"] { display: none; }
[data-testid="stMainBlockContainer"] {
  max-width: 74rem;
  padding-block: 2.75rem 5rem;
  padding-inline: 2rem;
}
"""

__all__ = ["SHELL"]
