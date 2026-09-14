"""Stage 0B — Annex IV validation, completeness gate, and T01b/T01c storage."""
from __future__ import annotations

from typing import Any

from aaa.agents.intake_validator.errors import COMPLETENESS_GATE, IntakeValidatorError
from aaa.agents.intake_validator.stage.artifact_kind import derive_artifact_kind
from aaa.agents.intake_validator.stage.completeness import completeness_content
from aaa.platform.state import ClientSubmission
from aaa.tools.annex_iv_validator import annex_iv_validator
from aaa.tools.intake_completeness_calculator import intake_completeness_calculator


def run_stage_b(agent: Any, engagement_id: str, stage_a_payload: dict[str, Any],
                stage_b_payload: dict[str, Any], declared_modality: str,
                art43_preview_procedure: str,
                ) -> tuple[ClientSubmission, Any, dict, str, str]:
    """Validate the dossier, compute completeness, and store T01b + T01c.

    :param agent: The IntakeValidator (evidence store + name).
    :param engagement_id: Engagement identifier.
    :param stage_a_payload: Validated Stage A payload (for the submission).
    :param stage_b_payload: Raw Stage B payload.
    :param declared_modality: Modality declared in Stage A.
    :param art43_preview_procedure: Stage A Art. 43 preview.
    :returns: ``(submission, completeness_report, t01c_content, t01b_uri, t01c_uri)``.
    :raises IntakeValidatorError: On validation failure or a failed gate.
    """
    derive_artifact_kind(stage_b_payload)
    validation = annex_iv_validator(stage_b_payload, declared_modality)
    if not validation.is_valid:
        raise IntakeValidatorError(
            stage="B", reason="Annex IV dossier failed schema/conditional validation.",
            details=validation.to_dict())

    t01b_uri = agent.store.store_artefact(
        engagement_id=engagement_id, phase="stage_b",
        artefact_type="T01b_annex_iv_dossier",
        content=stage_b_payload, agent_name=agent.name)

    submission: ClientSubmission = {
        "stage_a": stage_a_payload,  # type: ignore[typeddict-item]
        "stage_b": stage_b_payload,  # type: ignore[typeddict-item]
        "stage_c": None,
        "intake_completeness_score": 0.0,
    }
    completeness_report = intake_completeness_calculator(
        submission=submission, declared_modality=declared_modality,
        engagement_id=engagement_id)
    submission["intake_completeness_score"] = completeness_report.score

    t01c_content = completeness_content(completeness_report, art43_preview_procedure)
    t01c_uri = agent.store.store_artefact(
        engagement_id=engagement_id, phase="stage_b",
        artefact_type="T01c_intake_completeness_report",
        content=t01c_content, agent_name=agent.name)

    if not completeness_report.gate_passed:
        raise IntakeValidatorError(
            stage="B",
            reason=(f"intake_completeness_score={completeness_report.score:.2f} "
                    f"< {COMPLETENESS_GATE}. Remediate the listed fields before "
                    "Phase 1 can start."),
            details=completeness_report.to_dict())
    return submission, completeness_report, t01c_content, t01b_uri, t01c_uri
