"""Expanders — part of the widgets cascade layer."""
from __future__ import annotations

EXPANDERS = """
/* ---- expanders -------------------------------------------------------- */
.stApp [data-testid="stExpander"] details {
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  background: var(--surface);
  box-shadow: var(--shadow-1);
  overflow: clip;
}
.stApp [data-testid="stExpander"] summary {
  padding: 0.85rem 1.1rem;
  font-weight: 580;
  transition: background var(--dur-1) var(--ease);
}
.stApp [data-testid="stExpander"] summary:hover { background: var(--surface-2); }
"""

__all__ = ["EXPANDERS"]
