"""annex_iii_classify — deterministic Annex III use-case classifier (§3.6, §4.5).

Classifies an AI system against the Annex III high-risk use cases from its own
intake text, down to the sub-point, and records the words that support each
section. Provenance:

  - ``client_declared``  — declared in Stage A (kept even when the intake text
    offers no supporting term; its confidence then says so)
  - ``phase1_verified``  — not declared; the intake text evidences it
  - ``phase1_corrected`` / ``phase1_rejected`` — reserved for Phase 1 review

It no longer blends a regulatory-corpus similarity: that query carried the
section title, not the system, so it measured the law (T-20260913-043).

Usage::

    entries = annex_iii_classify(declared_sections=["5"],
                                 system_description="Credit scoring for retail customers.")
"""
from aaa.tools.annex_iii_classify.core import annex_iii_classify
from aaa.tools.annex_iii_classify.evidence import SectionEvidence, section_evidence
from aaa.tools.annex_iii_classify.logger import _SECTIONS_1_TO_4, logger
from aaa.tools.annex_iii_classify.make_entry import _keyword_score, _make_entry, _resolve_entry
from aaa.tools.annex_iii_classify.sections_5_to_8 import (
    _ANNEX_III_CATALOGUE,
    _SECTIONS_5_TO_8,
    NO_KEYWORD_EVIDENCE,
    _extract_marker,
    keyword_present,
    match_term,
)

__all__ = [
    "logger", "_SECTIONS_1_TO_4", "_SECTIONS_5_TO_8", "_ANNEX_III_CATALOGUE",
    "_extract_marker", "keyword_present", "match_term", "NO_KEYWORD_EVIDENCE",
    "SectionEvidence", "section_evidence",
    "_make_entry", "_resolve_entry", "_keyword_score", "annex_iii_classify",
]
