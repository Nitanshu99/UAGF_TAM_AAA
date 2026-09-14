"""The rows surface."""
from __future__ import annotations

ROWS = """
.aaa-article-row { display: grid; grid-template-columns: 1fr auto; gap: 0.5rem 1rem;
  align-items: center; padding: 0.72rem 0.2rem; border-block-end: 1px solid var(--surface-3); }
.aaa-article-row:last-child { border-block-end: 0; }
.aaa-article-row .subject { font-weight: 560; color: var(--text); }
.aaa-article-row .ref { font-size: 0.78rem; color: var(--text-3); }
.aaa-article-row .parts { grid-column: 1 / -1; display: grid; gap: 0.35rem;
  padding-inline-start: 0.9rem; border-inline-start: 2px solid var(--surface-3); }
.aaa-article-part { display: grid; grid-template-columns: 1fr auto; gap: 0.5rem 1rem;
  align-items: center; }
.aaa-article-part .subject { font-weight: 500; font-size: 0.9rem; }
.aaa-finding { border-inline-start: 3px solid var(--line-strong); background: var(--surface);
  border-radius: var(--r-md); padding: 0.85rem 1rem; box-shadow: var(--shadow-1);
  margin-block-end: 0.6rem; border-block: 1px solid var(--line);
  border-inline-end: 1px solid var(--line); }
.aaa-finding.material { border-inline-start-color: var(--bad); }
.aaa-finding.possibly_material { border-inline-start-color: var(--warn); }
.aaa-finding.observation { border-inline-start-color: var(--brand); }
.aaa-finding .fid { font-weight: 660; font-size: 0.78rem; color: var(--text-3);
  letter-spacing: 0.02em; }
.aaa-finding .body { color: var(--text); margin-block-start: 0.3rem; text-wrap: pretty; }
.aaa-finding .refs { font-size: 0.78rem; color: var(--text-3); margin-block-start: 0.35rem; }
.aaa-note { display: grid; grid-template-columns: auto 1fr; gap: 0.75rem;
  border-radius: var(--r-lg); padding: 1rem 1.15rem; border: 1px solid var(--line);
  background: var(--surface); box-shadow: var(--shadow-1); }
.aaa-note .glyph { font-size: 1.1rem; line-height: 1.4; }
.aaa-note .title { font-weight: 620; }
.aaa-note .text { color: var(--text-2); text-wrap: pretty; margin-block-start: 0.2rem; }
.aaa-note.is-info { background: var(--brand-soft); border-color: var(--brand-line); }
.aaa-note.is-warn { background: var(--warn-soft); border-color: color-mix(in oklab, var(--warn) 26%, white); }
.aaa-note.is-bad { background: var(--bad-soft); border-color: color-mix(in oklab, var(--bad) 24%, white); }
.aaa-note.is-ok { background: var(--ok-soft); border-color: color-mix(in oklab, var(--ok) 24%, white); }
"""

__all__ = ["ROWS"]
