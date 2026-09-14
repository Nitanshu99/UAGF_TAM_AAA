"""The Annex III catalogue by sub-point, and the flat keyword view derived from it."""
from __future__ import annotations

from aaa.tools.annex_iii_classify.points.first_half import POINTS_1_TO_4
from aaa.tools.annex_iii_classify.points.second_half import POINTS_5_TO_8

POINTS = {**POINTS_1_TO_4, **POINTS_5_TO_8}


def flat_sections(points: dict) -> dict[str, dict]:
    """``{section: {section_title, keywords}}`` — the shape the rest of the tool reads."""
    return {section: {"section_title": title,
                      "keywords": [term for _label, terms in subs.values() for term in terms]}
            for section, (title, subs) in points.items()}


__all__ = ["POINTS", "POINTS_1_TO_4", "POINTS_5_TO_8", "flat_sections"]
