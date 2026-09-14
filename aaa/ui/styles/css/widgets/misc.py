"""Misc — part of the widgets cascade layer."""
from __future__ import annotations

MISC = """
/* ---- misc ------------------------------------------------------------- */
.stApp [data-testid="stProgress"] div[role="progressbar"] > div { background: var(--brand); }
.stApp [data-testid="stMetricValue"] { color: var(--text); font-weight: 650; }
.stApp [data-testid="stMetricLabel"] p { color: var(--text-3); }
.stApp [data-baseweb="tag"] {
  background: var(--brand-soft);
  color: var(--brand-hover);
  border-radius: var(--r-pill);
}
.stApp .stCheckbox [data-baseweb="checkbox"] div:first-child { border-radius: 0.35rem; }
"""

__all__ = ["MISC"]
