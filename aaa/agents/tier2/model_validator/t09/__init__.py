"""T09 model card builder."""
from __future__ import annotations

from typing import Any, Mapping

from aaa.agents.tier2.model_validator.t09.limits import derive_limitations
from aaa.agents.tier2.model_validator.t09.performance import performance_section
from aaa.agents.tier2.model_validator.t09.questions import T09_QUESTIONS
from aaa.agents.tier2.model_validator.t09.reasons import not_measured_reason
from aaa.agents.tier2.model_validator.t09.sections import (
    architecture_section,
    identity_section,
    training_section,
)
from aaa.agents.tier2.model_validator.t09.usage import (
    ART13_NOTES,
    ETHICAL_CONSIDERATIONS,
    intended_use_section,
)
from aaa.tools.document_evidence import Evidence
from aaa.tools.model_meta.introspect import model_facts


def build_t09(
    engagement_id: str,
    t01a: dict[str, Any],
    t01b: dict[str, Any],
    modality: str,
    metrics_result: dict[str, Any],
    now: str,
    declared: dict[str, Any] | None = None,
    found: Mapping[str, Evidence | None] | None = None,
    model: Any = None,
) -> dict[str, Any]:
    """Build the T09 model card from the dossier plus metric_suite output.

    :param engagement_id: Engagement identifier.
    :param t01a: T01a triage artefact.
    :param t01b: T01b Annex IV dossier artefact.
    :param modality: Normalised system modality.
    :param metrics_result: Output of ``metric_suite``.
    :param now: ISO-8601 generation timestamp.
    :param declared: The provider's declared metrics block, unverified.
    :param found: Grounded answers to :data:`T09_QUESTIONS`.
    :param model: The model Phase 3 loaded, whose own attributes fill the architecture.
    :returns: T09 model-card dictionary.
    """
    model_type = t01b.get("model_type") or modality
    facts = model_facts(model)
    reason = not_measured_reason(metrics_result, t01b, model)
    return {
        "engagement_id": engagement_id,
        "model_identity": identity_section(t01a, model_type, modality),
        "architecture": architecture_section(t01b, model_type, found, facts, model),
        "training_regime": training_section(t01b, facts, model),
        "performance_metrics": performance_section(t01b, metrics_result, declared, reason),
        "intended_use": intended_use_section(t01a),
        "known_limitations": derive_limitations(modality, metrics_result, t01b, declared, reason),
        "ethical_considerations": ETHICAL_CONSIDERATIONS,
        "art13_compliance_notes": ART13_NOTES,
        "generated_at": now,
    }


__all__ = ["T09_QUESTIONS", "build_t09"]
