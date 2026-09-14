"""The pills surface."""
from __future__ import annotations

PILLS = """
.aaa-pill { display: inline-flex; align-items: center; gap: 0.38rem; font-size: 0.76rem;
  font-weight: 620; padding: 0.26rem 0.66rem; border-radius: var(--r-pill);
  border: 1px solid transparent; white-space: nowrap; }
.aaa-pill::before { content: ""; inline-size: 0.42rem; block-size: 0.42rem; border-radius: 50%;
  background: currentcolor; flex: none; }
/* A pill that carries its own glyph does not also need the generic dot — the
   glyph is the better shape cue, and two of them read as a stutter. */
.aaa-pill.has-glyph::before { content: none; }
.aaa-pill.is-ok { color: var(--ok); background: var(--ok-soft); border-color: color-mix(in oklab, var(--ok) 22%, white); }
.aaa-pill.is-warn { color: var(--warn); background: var(--warn-soft); border-color: color-mix(in oklab, var(--warn) 24%, white); }
.aaa-pill.is-bad { color: var(--bad); background: var(--bad-soft); border-color: color-mix(in oklab, var(--bad) 22%, white); }
.aaa-pill.is-none { color: var(--text-2); background: var(--none-soft); border-color: var(--line); }
.aaa-pill.is-info { color: var(--brand-hover); background: var(--brand-soft); border-color: var(--brand-line); }
"""

__all__ = ["PILLS"]
