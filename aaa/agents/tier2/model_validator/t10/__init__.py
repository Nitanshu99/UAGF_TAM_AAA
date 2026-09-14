"""T10 explainability report builder."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.model_validator.context import Explainability
from aaa.agents.tier2.model_validator.t10.interpretation import build_interpretation


def build_t10(engagement_id: str, modality: str, expl: Explainability,
              now: str) -> dict[str, Any]:
    """Build the T10 explainability report.

    :param engagement_id: Engagement identifier.
    :param modality: Normalised system modality.
    :param expl: Explainability evidence from step 3.
    :param now: ISO-8601 generation timestamp.
    :returns: T10 explainability-report dictionary.
    """
    skipped_reason: str | None = None
    if expl.degraded:
        skipped_reason = ("Explainability techniques could not be executed on the "
                          "supplied model: " + " ".join(expl.degraded))
    elif expl.techniques == ["none"]:
        skipped_reason = ("No trained model accessible — explainability "
                          "techniques could not be executed.")
    local = [_strip_diagnostics(e) for e in expl.local_expl]
    return {
        "engagement_id": engagement_id,
        "modality": modality,
        "techniques_applied": expl.techniques,
        "global_explanation": _strip_diagnostics(expl.global_expl),
        "local_explanations": local or None,
        "visual_explanations": expl.visual_expl or None,
        "interpretation": build_interpretation(modality, expl),
        "skipped_reason": skipped_reason,
        "art13_compliance_notes": _art13_note(expl.techniques),
        "generated_at": now,
    }


def _art13_note(techniques: list[str]) -> str:
    """What was applied, or that nothing was — never "applied: ['none']" (case 06)."""
    ran = [t for t in techniques if t != "none"]
    if not ran:
        return ("No explainability technique was applied, so no Art. 13 §1–§2 explainability "
                "evidence was collected; see skipped_reason.")
    return ("Explainability evidence collected per Art. 13 §1–§2 with: "
            f"{', '.join(ran)}.")


#: In-process keys the tools add for the agent; T10's sub-objects admit neither.
_DIAGNOSTIC_KEYS = frozenset({"degraded_reason", "explained_output", "vocabulary_size"})


def _strip_diagnostics(block: dict[str, Any]) -> dict[str, Any]:
    """Drop in-process diagnostic keys the T10 schema does not admit.

    ``degraded_reason`` is how the tools tell the agent they fell back; it
    reaches the model through ``tool_outputs`` and the ``skipped_reason``
    above, not through the artefact, whose sub-objects are
    ``additionalProperties: false``.
    """
    return {k: v for k, v in block.items() if k not in _DIAGNOSTIC_KEYS}


__all__ = ["build_t10"]
