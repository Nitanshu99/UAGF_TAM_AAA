"""Keyed containers used as cards — part of the widgets cascade layer."""
from __future__ import annotations

KEYED_CONTAINERS_USED_AS_CARDS = """
/* ---- keyed containers used as cards ---------------------------------- */
.stApp [class*="st-key-aaacard-"] {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  padding: 1.15rem 1.3rem;
  box-shadow: var(--shadow-1);
  block-size: 100%;
  animation: aaa-rise var(--dur-3) var(--ease) backwards;
  --anim-reduced: aaa-fade var(--dur-2) var(--ease) backwards;
}
"""

__all__ = ["KEYED_CONTAINERS_USED_AS_CARDS"]
