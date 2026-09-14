"""Surfaces — part of the base cascade layer."""
from __future__ import annotations

SURFACES = """
/* ---- surfaces --------------------------------------------------------- */
.aaa-card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  padding: 1.15rem 1.3rem;
  box-shadow: var(--shadow-1);
}
.aaa-stack > * + * { margin-block-start: 1rem; }
.aaa-grid { display: grid; gap: 0.85rem; }
.aaa-eyebrow {
  font-size: 0.72rem;
  font-weight: 650;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: var(--text-3);
}
.aaa-section-title { font-size: 1.22rem; font-weight: 640; letter-spacing: -0.015em; }
.aaa-section-sub { color: var(--text-2); font-size: 0.93rem; max-width: var(--measure); }
.aaa-muted { color: var(--text-3); font-size: 0.85rem; }
"""

__all__ = ["SURFACES"]
