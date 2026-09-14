"""Data tables — part of the base cascade layer."""
from __future__ import annotations

DATA_TABLES = """
/* ---- data tables ------------------------------------------------------ */
table.aaa-matrix { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
table.aaa-matrix th {
  text-align: start;
  color: var(--text-3);
  font-weight: 620;
  font-size: 0.74rem;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  padding: 0.45rem 0.7rem;
  border-block-end: 1px solid var(--line);
  text-wrap: balance;
}
table.aaa-matrix td {
  padding: 0.6rem 0.7rem;
  vertical-align: middle;
  color: var(--text-2);
}
table.aaa-matrix tbody tr:not(:last-child) td { border-block-end: 1px solid var(--surface-3); }
table.aaa-matrix tbody tr { transition: background var(--dur-1) var(--ease); }
table.aaa-matrix tbody tr:hover { background: var(--surface-2); }
.aaa-scroll-x { overflow-x: auto; }
"""

__all__ = ["DATA_TABLES"]
