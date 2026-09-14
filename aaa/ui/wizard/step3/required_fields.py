"""Which Stage A fields are always required, and which Stage B ones the modality adds."""
from __future__ import annotations

from aaa.tools.intake_completeness_calculator.section_weights import (
    _L_BRANCH_CONDITIONAL,
    _L_BRANCH_MODALITIES,
)
from aaa.ui.wizard.collect import collect_stage_a, collect_stage_b

#: Stage A fields the T01a schema requires to be non-empty, and the label the
#: form gives each one, so the warning names what the customer actually sees.
#: The three selects start undeclared (T-20260914-021), so they are listed too.
_REQUIRED_STAGE_A = {
    "provider_name": "Legal provider name",
    "system_name": "System name",
    "version": "Version",
    "intended_purpose": "Intended purpose",
    "declared_modality": "AI modality",
    "declared_risk_tier": "Self-assessed risk tier",
    "deployment_context": "Deployment context",
}
def _required_stage_a_blanks() -> list[str]:
    """Labels of the required Stage A fields that are still empty.

    :returns: Human-readable field labels, in form order.
    """
    stage_a = collect_stage_a()
    return [label for field, label in _REQUIRED_STAGE_A.items()
            if not str(stage_a.get(field) or "").strip()]
#: Conditional Stage B field → the label its uploader carries in the form.
_CONDITIONAL_LABELS = {
    "system_prompt_uri": "System prompt",
    "rag_manifest_uri": "RAG manifest",
    "guardrail_config_uri": "Guardrail configuration",
    "golden_set_uri": "Golden evaluation set",
    "tool_inventory": "Tool inventory",
}
def _conditional_stage_b_blanks() -> list[str]:
    """Labels of the Stage B fields this modality requires and does not have.

    The 0.80 completeness score weights the nine Annex IV sections and knows
    nothing about the modality-conditional set (M29), so declaring ``llm`` and
    running produced a Stage B schema failure *after* the customer committed to
    the audit — the same late failure M27 fixed for Stage A, one layer down.

    :returns: Human-readable labels, in the order the form shows them.
    """
    stage_a, stage_b = collect_stage_a(), collect_stage_b()
    modality = str(stage_a.get("declared_modality") or "")
    if modality not in _L_BRANCH_MODALITIES:
        return []
    return [label for field, label in _CONDITIONAL_LABELS.items()
            if field in _L_BRANCH_CONDITIONAL
            and (_L_BRANCH_CONDITIONAL[field] != "agentic" or modality == "agentic")
            and not stage_b.get(field)]


__all__ = ["_CONDITIONAL_LABELS", "_REQUIRED_STAGE_A", "_conditional_stage_b_blanks", "_required_stage_a_blanks"]
