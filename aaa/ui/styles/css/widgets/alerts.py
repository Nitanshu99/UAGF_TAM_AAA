"""Alerts — part of the widgets cascade layer."""
from __future__ import annotations

ALERTS = """
/* ---- alerts ----------------------------------------------------------- */
/* The tint belongs on the container, not on the content element inside it:
   painting the inner one left Streamlit's own tint showing round the edge, so
   every warning rendered as a pink panel inside a yellow one. `:has()` picks
   the container by the kind marker its child carries. */
.stApp [data-testid="stAlert"] {
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-1);
}
.stApp [data-testid="stAlertContainer"] {
  border-radius: var(--r-lg);
  border: 1px solid var(--line);
  color: var(--text);
}
.stApp :is([data-testid^="stAlertContent"]) { background: transparent; color: inherit; }
.stApp [data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) {
  background: var(--brand-soft);
  border-color: var(--brand-line);
}
.stApp [data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) {
  background: var(--ok-soft);
  border-color: color-mix(in oklab, var(--ok) 24%, white);
}
.stApp [data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) {
  background: var(--warn-soft);
  border-color: color-mix(in oklab, var(--warn) 26%, white);
}
.stApp [data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) {
  background: var(--bad-soft);
  border-color: color-mix(in oklab, var(--bad) 24%, white);
}
"""

__all__ = ["ALERTS"]
