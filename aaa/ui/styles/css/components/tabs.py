"""The tabs surface."""
from __future__ import annotations

TABS = """
.stApp [data-baseweb="tab-list"] { gap: 1.4rem; border-block-end: 1px solid var(--line); }
.stApp [data-baseweb="tab"] { padding-inline: 0; }
.stApp [data-baseweb="tab"] p { font-weight: 560; color: var(--text-3); }
.stApp [aria-selected="true"] p { color: var(--brand); font-weight: 640; }
.stApp [data-baseweb="tab-highlight"] { background: var(--brand); block-size: 2px; }
.stApp [data-baseweb="tab-border"] { display: none; }
"""

__all__ = ["TABS"]
