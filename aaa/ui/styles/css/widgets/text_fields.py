"""Text fields — part of the widgets cascade layer."""
from __future__ import annotations

TEXT_FIELDS = """
/* ---- text fields ------------------------------------------------------ */
.stApp :is(.stTextInput, .stTextArea, .stNumberInput) [data-baseweb="base-input"],
.stApp :is(.stTextInput, .stTextArea, .stNumberInput) > div > div {
  background: var(--surface);
  border-radius: var(--r-md);
}
.stApp :where(input, textarea) {
  color: var(--text) !important;
  /* Never below 1rem: iOS Safari zooms the page when a focused field is
     smaller, which throws the layout on every tap. */
  font-size: 1rem;
}
.stApp :where(input, textarea)::placeholder { color: var(--text-3); }
.stApp [data-baseweb="input"], .stApp [data-baseweb="textarea"], .stApp [data-baseweb="select"] > div {
  border: 1px solid var(--control-line);
  border-radius: var(--r-md);
  background: var(--surface);
  transition: border-color var(--dur-1) var(--ease), box-shadow var(--dur-1) var(--ease);
}
.stApp :where([data-baseweb="input"], [data-baseweb="textarea"]):focus-within,
.stApp [data-baseweb="select"] > div:focus-within {
  border-color: var(--brand);
  box-shadow: 0 0 0 3px var(--brand-soft);
}
.stApp textarea { resize: vertical; }
.stApp [data-testid="stWidgetLabel"] p { font-weight: 560; color: var(--text); font-size: 0.9rem; }
"""

__all__ = ["TEXT_FIELDS"]
