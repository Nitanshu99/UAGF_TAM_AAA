"""Typography — part of the base cascade layer."""
from __future__ import annotations

TYPOGRAPHY = """
/* ---- typography ------------------------------------------------------- */
.stApp, [data-testid="stMarkdownContainer"] {
  font-family: ui-sans-serif, -apple-system, "Segoe UI", Inter, system-ui, sans-serif;
  color: var(--text);
  font-size-adjust: 0.52;
}
.stApp :where(h1, h2, h3, h4) {
  color: var(--text);
  letter-spacing: -0.021em;
  text-wrap: balance;
  font-weight: 640;
}
.stApp h1 { font-size: clamp(1.9rem, 1.3rem + 1.7vw, 2.6rem); line-height: 1.12; }
.stApp h2 { font-size: clamp(1.35rem, 1.1rem + 0.8vw, 1.7rem); line-height: 1.2; }
.stApp h3 { font-size: 1.1rem; line-height: 1.3; }
.stApp p, .stApp li { line-height: 1.6; text-wrap: pretty; }
[data-testid="stMarkdownContainer"] > p { max-width: var(--measure); color: var(--text-2); }
.stApp a:not(:where(.aaa-btn, .aaa-tab)) { color: var(--brand); text-underline-offset: 0.18em; }
.stApp code {
  font-size: 0.85em;
  background: var(--surface-3);
  color: var(--text-2);
  padding: 0.12em 0.38em;
  border-radius: var(--r-sm);
}
.stApp hr { border-color: var(--line); margin-block: 1.6rem; }
"""

__all__ = ["TYPOGRAPHY"]
