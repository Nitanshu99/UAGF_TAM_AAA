"""Part 4 of the former ``intake_completeness_calculator`` module (auto-split)."""
from __future__ import annotations

from aaa.platform.state import ClientSubmission
from aaa.tools.intake_completeness_calculator.field_present import (  # noqa: F401
    _field_present,
    _score_sections,
)
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


def intake_completeness_calculator(
    submission: ClientSubmission,
    declared_modality: str,
    engagement_id: str = "",
) -> CompletenessReport:
    """
    Computes the weighted Annex IV completeness score (KPI 0).

    Args:
        submission: The full ClientSubmission (Stage A + B).
        declared_modality: Modality declared in Stage A.
        engagement_id: Engagement identifier for the report.

    Returns:
        CompletenessReport with .score and .gate_passed.
    """
    # Plain-dict view: the section scorers take dict[str, Any], which pyright
    # will not accept a TypedDict for.
    dossier = dict(submission["stage_b"])
    is_l_branch = declared_modality in _L_BRANCH_MODALITIES
    is_agentic = declared_modality == "agentic"

    section_scores, missing_required, total_score = _score_sections(dossier)

    missing_conditional: list[ConditionalField] = []
    for fname, condition in _L_BRANCH_CONDITIONAL.items():
        applicable = is_l_branch if "agentic" not in condition else is_agentic
        present = _field_present(dossier, fname)
        missing_conditional.append(ConditionalField(field=fname, condition=condition, applicable=applicable))
        if applicable and not present:
            # Conditional required fields reduce the score by their section weight / n_fields
            total_score = max(0.0, total_score - 0.02)

    score = round(min(total_score, 1.0), 2)
    return CompletenessReport(
        engagement_id=engagement_id,
        score=score,
        section_scores=section_scores,
        missing_required=missing_required,
        missing_conditional=missing_conditional,
        gate_passed=score >= GATE_THRESHOLD,
    )
