"""Part 2 of the former ``intake_completeness_calculator`` module (auto-split)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aaa.tools.intake_completeness_calculator.section_weights import (  # noqa: F401
    _L_BRANCH_CONDITIONAL,
    _L_BRANCH_MODALITIES,
    _SECTION_FIELDS,
    GATE_THRESHOLD,
    SECTION_WEIGHTS,
    SectionScore,
)


@dataclass
class MissingField:
    """A required field absent from the intake dossier."""

    field: str
    section: int
    reason: str


@dataclass
class ConditionalField:
    """A conditionally-required field and whether it applies to the modality."""

    field: str
    condition: str
    applicable: bool


@dataclass
class CompletenessReport:
    """Output contract for intake_completeness_calculator."""
    engagement_id: str
    score: float
    section_scores: dict[str, SectionScore]
    missing_required: list[MissingField]
    missing_conditional: list[ConditionalField]
    gate_passed: bool

    def to_dict(self) -> dict[str, Any]:
        """Return the report as a JSON-serialisable dict (the T01c contract)."""
        return {
            "engagement_id": self.engagement_id,
            "intake_completeness_score": self.score,
            "section_scores": {
                k: {"score": v.score, "weight": v.weight, "label": v.label}
                for k, v in self.section_scores.items()
            },
            "missing_required_fields": [
                {"field": f.field, "section": f.section, "reason": f.reason}
                for f in self.missing_required
            ],
            "missing_conditional_fields": [
                {"field": f.field, "condition": f.condition, "applicable": f.applicable}
                for f in self.missing_conditional
            ],
            "gate_passed": self.gate_passed,
        }
