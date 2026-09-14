"""The inputs a cyber spawn probes: the T11 it extends, and the scored evaluation set."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier3.cyber_agent.template import T11
from aaa.tools.eval_inputs import load_scored_evaluation
from aaa.tools.system_prompt_text import resolve_system_prompt


def cyber_inputs(agent: Any, decl: dict, engagement_id: str) -> tuple[dict, str, list, Any]:
    """Load the T11 this spawn extends, its probes, and the scored evaluation set.

    Phase 3 owns the loading findings, so they are suppressed here: this spawn
    only needs the inputs. The system prompt is resolved onto *decl* in place
    when the dispatch did not already carry it.

    :param agent: The spawn agent, holding the evidence store.
    :param decl: The dispatch's ``declaration_summary``; mutated in place.
    :param engagement_id: Engagement identifier.
    :returns: ``(t11, base_uri, probes, scored)``.
    """
    t11_ref = decl.get("phase_artefacts", {}).get(T11) or {}
    base_uri = t11_ref.get("uri", "") if isinstance(t11_ref, dict) else ""
    t11 = (agent.store.get_artefact(base_uri) or {}) if base_uri else {}

    # Phase 3 owns the loading findings; this spawn only needs the inputs.
    scored = load_scored_evaluation(
        agent.store, decl.get("stage_b") or {}, emit_load_findings=False,
        emit_datadict_findings=False, source_phase="Cyber")
    probes = list(t11.get("probes", []))
    if not decl.get("system_prompt_text"):
        decl["system_prompt_text"] = resolve_system_prompt(
            decl.get("stage_b") or {}, agent.store)
    return t11, base_uri, probes, scored


__all__ = ["cyber_inputs"]
