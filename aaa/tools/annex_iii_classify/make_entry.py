"""Turning section evidence into a T03 entry with provenance and confidence."""
from __future__ import annotations

from aaa.platform.state import AnnexIIIEntry
from aaa.tools.annex_iii_classify import sections_5_to_8 as ladder
from aaa.tools.annex_iii_classify.evidence import SectionEvidence
from aaa.tools.annex_iii_classify.sections_5_to_8 import _ANNEX_III_CATALOGUE, keyword_present


def _make_entry(section: str, evidence: SectionEvidence, provenance: str,
                confidence: float) -> AnnexIIIEntry:
    """Build one :class:`AnnexIIIEntry` for *section*.

    ``derogation_claimed`` is filled from Stage A by the scope agent.
    """
    return AnnexIIIEntry(
        annex_iii_section=section,  # type: ignore[arg-type]
        section_title=_ANNEX_III_CATALOGUE[section]["section_title"],
        use_case_marker=evidence.marker(section),
        confidence=confidence,
        provenance=provenance,  # type: ignore[arg-type]
        derogation_claimed=False,
        derogation_rationale=None,
    )


def _resolve_entry(section: str, evidence: SectionEvidence,
                   in_declared: bool) -> AnnexIIIEntry | None:
    """Apply the confidence ladder (see :mod:`.sections_5_to_8`) to one section.

    :returns: The entry, or ``None`` for an undeclared section without enough evidence.
    """
    if in_declared:
        confidence = (ladder.DECLARED_EVIDENCED if evidence.point
                      else ladder.DECLARED_SECTION_TERMS_ONLY if evidence.matched
                      else ladder.DECLARED_UNEVIDENCED)
        return _make_entry(section, evidence, "client_declared", confidence)
    if evidence.point and evidence.distinct_hits >= 2:
        return _make_entry(section, evidence, "phase1_verified", ladder.DETECTED)
    return None


def _keyword_score(keywords: list[str], text: str) -> float:
    """Fraction of *keywords* present in *text*, under the word-boundary rule (fix F14)."""
    if not keywords:
        return 0.0
    return sum(1 for kw in keywords if keyword_present(kw, text)) / len(keywords)
