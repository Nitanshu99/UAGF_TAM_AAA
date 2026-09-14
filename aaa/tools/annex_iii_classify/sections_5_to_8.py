"""Term matching, the flat view of points 5-8, and the confidence ladder.

**Confidence ladder** (T-20260913-043). Confidence states what supports a
section, not a floor: it was ``max(score, 0.75)``, the same 0.75 for a declared
section with evidence and without, and the "semantic" part of the score queried
the regulatory corpus with the section title — measuring the law, never the
system. Now:

* declared, a sub-point evidenced in the intake text → 0.9
* declared, only section-level terms → 0.7
* declared, nothing in the intake text → 0.5 — the declaration stands (a
  keyword list is no ground to lower a provider's own high-risk declaration) but
  it is recorded as unconfirmed
* not declared, two distinct terms including a sub-point → 0.7, ``phase1_verified``
"""
from __future__ import annotations

from typing import Any

from aaa.tools.annex_iii_classify.logger import _SECTIONS_1_TO_4
from aaa.tools.annex_iii_classify.points import POINTS_5_TO_8, flat_sections
from aaa.tools.term_match import match_term

_SECTIONS_5_TO_8: dict[str, dict[str, Any]] = flat_sections(POINTS_5_TO_8)
_ANNEX_III_CATALOGUE: dict[str, dict[str, Any]] = {**_SECTIONS_1_TO_4, **_SECTIONS_5_TO_8}

DECLARED_EVIDENCED = 0.9
DECLARED_SECTION_TERMS_ONLY = 0.7
DECLARED_UNEVIDENCED = 0.5
DETECTED = 0.7

#: Marker when no term appears. No semantic match is performed, so none is claimed.
NO_KEYWORD_EVIDENCE: str = "no supporting term in the intake text"


def keyword_present(keyword: str, text: str) -> bool:
    """Whether *keyword* occurs in *text* as a word, not as a substring (fix F14)."""
    return match_term(keyword, text) is not None


def _extract_marker(keywords: list[str], text: str) -> str:
    """The first catalogue keyword present, or :data:`NO_KEYWORD_EVIDENCE`."""
    return next((kw for kw in keywords if keyword_present(kw, text)), NO_KEYWORD_EVIDENCE)
