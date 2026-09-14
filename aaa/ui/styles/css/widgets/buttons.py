"""Buttons — the base rule and its interaction states."""
from __future__ import annotations

BUTTONS_BASE = """

/* ---- buttons ---------------------------------------------------------- */
/* `--btn` is the one selector every button rule is written against, so the
   primary variant can out-specify the base without either of them having to
   grow a chain of ancestors. */
.stApp :is(.stButton, .stDownloadButton, .stFormSubmitButton) button {
  border-radius: var(--r-pill);
  border: 1px solid var(--control-line);
  background: var(--surface);
  color: var(--text);
  font-weight: 560;
  min-block-size: 2.6rem;
  padding-inline: 1.15rem;
  box-shadow: var(--shadow-1);
  transition: background var(--dur-1) var(--ease), border-color var(--dur-1) var(--ease),
              translate var(--dur-1) var(--ease), box-shadow var(--dur-1) var(--ease);
}
.stApp :is(.stButton, .stDownloadButton, .stFormSubmitButton) button:hover:not(:disabled) {
  border-color: var(--brand-line);
  background: var(--brand-soft);
  color: var(--brand-hover);
  translate: 0 -1px;
}
.stApp :is(.stButton, .stDownloadButton, .stFormSubmitButton) button:active:not(:disabled) {
  translate: 0 0;
}
.stApp :is(.stButton, .stFormSubmitButton, .stDownloadButton) button:disabled {
  opacity: 1;
  color: var(--text-3);
  background: var(--surface-2);
  border-color: var(--line);
  box-shadow: none;
}
"""

__all__ = ["BUTTONS_BASE"]
