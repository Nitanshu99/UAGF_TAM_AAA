"""browser-generated UI — one ``:root`` block; multiple blocks cascade identically."""
from __future__ import annotations

BROWSER_GENERATED_UI = """
:root {
/* ---- browser-generated UI ---- */
  accent-color: var(--brand);
  scrollbar-color: var(--line-strong) transparent;
}

/* The two tones must survive Forced Colors Mode as *structure*, even though
   the hues themselves are replaced by the user's system palette. */
@media (forced-colors: active) {
  :root {
    --line: CanvasText;
    --line-strong: CanvasText;
    --brand: LinkText;
  }
}
"""

__all__ = ["BROWSER_GENERATED_UI"]
