"""What in the intake text supports one Annex III section, down to the sub-point."""
from __future__ import annotations

from dataclasses import dataclass

from aaa.tools.annex_iii_classify.points import POINTS
from aaa.tools.annex_iii_classify.sections_5_to_8 import NO_KEYWORD_EVIDENCE, match_term


@dataclass(frozen=True)
class SectionEvidence:
    """The best-supported sub-point, the text that supports it, and how many terms hit."""

    point: str | None
    label: str
    matched: str | None
    distinct_hits: int

    def marker(self, section: str) -> str:
        """The T03 ``use_case_marker``: sub-point, what it covers, and the words found."""
        if self.matched is None:
            return NO_KEYWORD_EVIDENCE
        if self.point is None:
            return f'§{section} (sub-point not identified): "{self.matched}"'
        return f'§{section}({self.point}) {self.label}: "{self.matched}"'


def section_evidence(section: str, text: str) -> SectionEvidence:
    """Match every term of *section* against *text*; prefer a specific sub-point.

    :param section: Annex III point number.
    :param text: Lower-cased intake text.
    """
    _title, subs = POINTS[section]
    hits = [(point, label, found) for point, (label, terms) in subs.items()
            for term in terms if (found := match_term(term, text))]
    distinct = len({found for _p, _l, found in hits})
    specific = [(p, label, found) for p, label, found in hits if p != "*"]
    if specific:
        return SectionEvidence(specific[0][0], specific[0][1], specific[0][2], distinct)
    if hits:
        return SectionEvidence(None, "", hits[0][2], distinct)
    return SectionEvidence(None, "", None, 0)


__all__ = ["SectionEvidence", "section_evidence"]
