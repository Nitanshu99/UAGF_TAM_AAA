"""Resolving the L-branch's inputs and measuring the T16 evidence."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier3.uagf_tam_l.declared_controls import resolve_declared_controls
from aaa.agents.tier3.uagf_tam_l.evals import eval_inputs
from aaa.agents.tier3.uagf_tam_l.golden_set import resolve_golden_set
from aaa.agents.tier3.uagf_tam_l.ragas_budget import bounded_ragas
from aaa.agents.tier3.uagf_tam_l.t16 import build_t16
from aaa.agents.tier3.uagf_tam_l.trace_sample import resolve_trace_sample
from aaa.tools.system_prompt_text import resolve_system_prompt


async def gather_t16(agent: Any, decl: dict[str, Any], engagement_id: str,
                     modality: str) -> dict[str, Any]:
    """Resolve the golden set, traces, controls and prompt, and build T16 from them.

    :param agent: The L-branch agent (evidence store, name for the budget).
    :param decl: Declaration summary; ``system_prompt_text`` is filled when absent.
    :param engagement_id: Engagement identifier.
    :param modality: Verified modality.
    :returns: The T16 payload.
    """
    stage_b = decl.get("stage_b") or {}
    resolved_golden_set = resolve_golden_set(stage_b, agent.store)
    questions, contexts, answers, expected = eval_inputs(decl, resolved_golden_set)
    trace_sample = (resolve_trace_sample(stage_b, agent.store)
                    if modality == "agentic" else None)
    declared_controls = resolve_declared_controls(stage_b, agent.store)
    # `system_prompt_text` is read by `build_t16` and was never written by
    # anyone, so the client's uploaded prompt was never analysed.
    if not decl.get("system_prompt_text"):
        decl["system_prompt_text"] = resolve_system_prompt(stage_b, agent.store)

    ragas_metrics = await bounded_ragas(agent, questions, contexts, answers, expected)
    t16 = build_t16(decl, engagement_id, modality, questions, contexts,
                    answers, expected, trace_sample, declared_controls, ragas_metrics)
    return t16


__all__ = ["gather_t16"]
