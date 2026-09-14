"""Part 3 of the former ``intake_completeness_calculator`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.tools.intake_completeness_calculator.missingfield import (  # noqa: F401
    CompletenessReport,
    ConditionalField,
    MissingField,
)
from aaa.tools.intake_completeness_calculator.section_weights import (  # noqa: F401
    _L_BRANCH_CONDITIONAL,
    _L_BRANCH_MODALITIES,
    _SECTION_FIELDS,
    GATE_THRESHOLD,
    SECTION_WEIGHTS,
    SectionScore,
)


def _field_present(dossier: dict[str, Any], field_name: str) -> bool:
    val = dossier.get(field_name)
    if val is None:
        return False
    if isinstance(val, (str, list, dict)):
        return bool(val)
    return True


def _score_sections(dossier: dict[str, Any],
                    ) -> tuple[dict[str, "SectionScore"], list["MissingField"], float]:
    """Score every Annex IV section against the dossier.

    :param dossier: Stage B payload.
    :returns: ``(section_scores, missing_required, total_score)``.
    """
    section_scores: dict[str, SectionScore] = {}
    missing_required: list[MissingField] = []
    total_score = 0.0
    for section, fields in _SECTION_FIELDS.items():
        weight = SECTION_WEIGHTS[section]
        present = [f for f in fields if _field_present(dossier, f)]
        frac = len(present) / len(fields) if fields else 1.0
        total_score += weight * frac
        section_scores[str(section)] = SectionScore(
            score=round(frac, 4), weight=weight, label=f"Annex IV §{section}")
        for f in fields:
            if not _field_present(dossier, f):
                missing_required.append(
                    MissingField(field=f, section=section, reason="Empty or missing"))
    return section_scores, missing_required, total_score
