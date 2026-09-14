"""Stage 0A — triage validation, scope gate, and Art. 43 preview."""
from __future__ import annotations

from typing import Any

from aaa.agents.intake_validator.errors import IntakeValidatorError
from aaa.platform.state import Art43Decision
from aaa.tools.art43_select import art43_select_from_state
from aaa.tools.triage_render import triage_render


def preview_art43(stage_a: dict[str, Any]) -> Art43Decision:
    """Compute the preview Art. 43 decision from declared Stage A values."""
    pseudo_state = {
        "declared_risk_tier": stage_a.get("declared_risk_tier", "minimal"),
        "declared_annex_iii_sections": stage_a.get("declared_annex_iii_sections", []),
        "provider_elects_third_party": stage_a.get("provider_elects_third_party", False),
        "risk_tier": stage_a.get("declared_risk_tier", "minimal"),
        "annex_iii_mapping": [],
        "harmonised_standards_applied": False,
        # The Stage A contract key is `annex_i_section_a` (T-20260913-016).
        "annex_i_section_a_acts": list(stage_a.get("annex_i_section_a", []) or []),
    }
    return art43_select_from_state(pseudo_state, use_declared=True)


def run_stage_a(agent: Any, engagement_id: str,
                stage_a_payload: dict[str, Any]) -> tuple[dict, str, str]:
    """Validate the triage form, apply the scope gate, and store T01a.

    :param agent: The IntakeValidator (evidence store + name).
    :param engagement_id: Engagement identifier.
    :param stage_a_payload: Raw Stage A payload.
    :returns: ``(scope_gate, art43_preview_procedure, t01a_uri)``.
    :raises IntakeValidatorError: On schema failure or a halting scope gate.
    """
    triage_result = triage_render(stage_a_payload)
    if not triage_result.is_valid:
        raise IntakeValidatorError(
            stage="A", reason="Triage form failed schema validation.",
            details={"schema_errors": triage_result.schema_errors})

    # Halt engagement if scope gate raises a red flag (prohibited/excluded).
    gate = (triage_result.rendered or {}).get("scope_gate", {})
    if gate.get("halt_engagement"):
        raise IntakeValidatorError(
            stage="A", reason=f"Scope gate halted engagement: {gate.get('verdict')}",
            details={"reasoning": gate.get("reasoning", [])})

    # Compute preview Art. 43 decision from declared values.
    art43_preview_procedure = preview_art43(stage_a_payload)["procedure"]
    stage_a_payload["art43_preview"] = art43_preview_procedure
    triage_result.rendered["art43_preview"] = art43_preview_procedure  # type: ignore[index]

    t01a_uri = agent.store.store_artefact(
        engagement_id=engagement_id, phase="stage_a",
        artefact_type="T01a_stage_a_triage",
        content=triage_result.rendered, agent_name=agent.name)
    return gate, art43_preview_procedure, t01a_uri
