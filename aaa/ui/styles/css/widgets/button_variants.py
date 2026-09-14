"""Buttons — the primary/secondary variants, the download button, and the touch target."""
from __future__ import annotations

BUTTON_VARIANTS = """
.stApp :is(.stButton, .stDownloadButton, .stFormSubmitButton)
  [data-testid^="stBaseButton-primary"] {
  background: var(--brand);
  border-color: transparent;
  color: #fff;
  box-shadow: var(--shadow-brand);
}
.stApp :is(.stButton, .stDownloadButton, .stFormSubmitButton)
  [data-testid^="stBaseButton-primary"]:hover:not(:disabled) {
  background: var(--brand-hover);
  border-color: transparent;
  color: #fff;
  box-shadow: var(--shadow-2);
}
.stApp .stDownloadButton button { inline-size: 100%; justify-content: center; }

@media (pointer: coarse) {
  .stApp :is(.stButton, .stDownloadButton, .stFormSubmitButton) button {
    min-block-size: 3rem;
  }
  .stApp [data-testid="stExpander"] summary { padding-block: 1rem; }
}

/* A control's label is markup, not body copy: it inherits the control's own
   colour and is not capped to the reading measure. */
.stApp :is(button, [data-testid="stAlertContainer"]) :is(p, span, div) {
  color: inherit;
  max-width: none;
}
"""

__all__ = ["BUTTON_VARIANTS"]
