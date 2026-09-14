"""T-20260914-009: every article key the code emits reads as a subject, not an id.

Case 03's results page listed "Art.27 / Art.27" — Art. 27 had no plain-language title.
"""
from __future__ import annotations

import re
from pathlib import Path

from aaa.agents.tier2.client_brief.constants import ARTICLE_TITLES

_KEY = re.compile(r'"((?:Art\.\d+[a-z]?(?:§\d+(?:\([a-z]\))?)?)|Annex_[IVX]+|GPAI_\d+)"')


def test_every_emitted_article_key_has_a_title() -> None:
    """A key written anywhere under aaa/ must be in ARTICLE_TITLES."""
    root = Path(__file__).resolve().parents[2] / "aaa"
    keys = {k for f in root.rglob("*.py") for k in _KEY.findall(f.read_text("utf-8"))}
    assert sorted(k for k in keys if k not in ARTICLE_TITLES) == []
