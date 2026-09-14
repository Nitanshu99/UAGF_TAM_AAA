"""Recording a phase whose artefacts were assembled without reaching a model."""
from __future__ import annotations

from aaa.agents.tier1.phases.verification.logger import logger


def _record_fallback_phase(state: dict, rep: dict, tids: list[str],
                           phase_id: str, phase_label: str) -> None:
    """Record on *state* that this phase's artefacts were written without the model.

    A phase agent fails soft: when its LLM call cannot be made it assembles its
    artefacts deterministically and returns a Report like any other, so the
    phase logs "complete" and the Verifier admits what it produced. The only
    trace is the ``prompt_runtime`` tool call carrying
    ``llm_fallback_mode=true`` — which travelled into the artefact narrative and
    nowhere a consumer of the delivered state would look.

    On the 2026-09-10 post-fix run the ScopeAgent's single call failed after one
    retry, and Phase 1 — the system card, the Annex III mapping, the risk tier
    and the Art. 43 decision — was machine-assembled. ``run_integrity`` reported
    ``degraded_phases: []`` and ``stub_artefact_ids: []``, both true and both
    beside the point. That run was marked unfit only because two *Verifier*
    calls had also failed; had they succeeded it would have been stamped
    ``suitable_for_handoff: True`` over a Phase 1 that never reached a model.

    This is the limit :func:`~aaa.platform.state.run_integrity.fallback_critique_ids`
    named and did not close — an artefact nothing *wrote*, as against one
    nothing checked.
    """
    note = next((str(call.get("result") or "") for call in (rep.get("tool_calls") or [])
                 if isinstance(call, dict) and call.get("tool") == "prompt_runtime"), "")
    if "llm_fallback_mode=true" not in note.lower():
        return
    logger.error(
        "%s: the agent's prompt runtime fell back, so %s were assembled "
        "deterministically rather than written by the model. The phase is "
        "complete; its artefacts are not model-authored.",
        phase_label, ", ".join(tids) or "its artefacts")
    state.setdefault("fallback_phases", []).append(
        {"phase_id": phase_id, "phase_label": phase_label, "template_ids": list(tids)})


__all__ = ["_record_fallback_phase"]
