"""Focus — part of the base cascade layer."""
from __future__ import annotations

FOCUS = """
/* ---- focus ------------------------------------------------------------ */
.stApp :where(button, a, input, textarea, select, summary, [tabindex]):focus-visible {
  outline: 2px solid var(--brand);
  outline-offset: 2px;
  border-radius: var(--r-sm);
}
"""

__all__ = ["FOCUS"]
