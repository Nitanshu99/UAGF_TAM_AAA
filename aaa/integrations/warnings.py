"""The warnings a hand-off carries about the model and the integrity of the run behind it."""
from __future__ import annotations

from typing import Any

from aaa.platform.state.model_vocab import REFERENCE_MODES
from aaa.tools.model_meta import DIRECTORY

#: The artefact Phase 1 is contracted to deliver. Every downstream verdict rests
#: on the scope it establishes, so its absence invalidates the verdict rather
#: than merely reducing the evidence behind it.
_PHASE_1_CONTRACT = "T02_system_card"
#: ``model_reference`` keys S6 cannot resolve a vendor model without.
_REFERENCE_KEYS = ("provider", "model_id", "revision")


def _model_warnings(stage_b: dict[str, Any]) -> list[str]:
    """Warn about fields S6 needs to obtain a runnable model."""
    mode = stage_b.get("model_access_mode")
    if mode in REFERENCE_MODES:
        reference = stage_b.get("model_reference") or {}
        return [
            f"stage_b.model_reference.{key} missing — required to resolve the "
            f"model under model_access_mode '{mode}'"
            for key in _REFERENCE_KEYS if not reference.get(key)
        ]
    if not stage_b.get("model_artifact_uri"):
        return []
    warnings = [
        f"stage_b.{field} missing — required when a model artefact is supplied"
        for field in ("task_type", "model_format", "model_artifact_kind")
        if not stage_b.get(field)
    ]
    # F7: an entrypoint is what makes a bundle loadable. Without it S6 has a
    # directory and no way to know which file in it is the model.
    if stage_b.get("model_artifact_kind") == DIRECTORY and not stage_b.get("model_entrypoint"):
        warnings.append(
            "stage_b.model_entrypoint missing — required when model_artifact_kind is "
            "'directory'; the model path is model_artifact_uri / model_entrypoint")
    return warnings
def _integrity_warnings(state: dict[str, Any], integrity: dict[str, Any]) -> list[str]:
    """Warn when the run did not produce the artefacts it is handing over.

    :param state: The audit state.
    :param integrity: The computed ``run_integrity`` block.
    :returns: Warnings naming the degraded phases, most severe first.
    """
    if integrity["suitable_for_handoff"]:
        return []
    warnings = [
        f"run is DEGRADED — {len(integrity['stub_artefact_ids'])} of "
        f"{integrity['artefact_count']} artefacts are placeholders; phase(s) "
        f"{', '.join(integrity['degraded_phases'])} delivered nothing. "
        f"Artefact URIs from those phases resolve to nothing."
    ]
    if _PHASE_1_CONTRACT in integrity["stub_artefact_ids"] and state.get("final_verdict"):
        warnings.append(
            f"final_verdict '{state['final_verdict']}' was reached without Phase 1 — "
            f"{_PHASE_1_CONTRACT} is a placeholder, so the scope, risk tier and "
            f"Annex III mapping the verdict rests on were never established")
    if integrity["unwired_agents"]:
        warnings.append("agents that failed to construct: "
                        + ", ".join(integrity["unwired_agents"]))
    return warnings


__all__ = ["_integrity_warnings", "_model_warnings"]
