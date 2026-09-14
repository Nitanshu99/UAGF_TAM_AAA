"""T16 evidence assembly for the UAGF-TAM-L branch."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aaa.agents.tier3.uagf_tam_l.ragas_run import derive_verdict, run_golden_set
from aaa.tools.groundedness_check import groundedness_check
from aaa.tools.prompt_injection_suite import prompt_injection_suite
from aaa.tools.ragas_eval import ragas_eval
from aaa.tools.trajectory_audit import trajectory_audit


def build_t16(decl: dict[str, Any], engagement_id: str, modality: str,
              questions: list, contexts: list, answers: list, expected: list,
              trace_sample: list | None = None,
              declared_controls: dict[str, Any] | None = None,
              ragas_metrics: dict[str, Any] | None = None,
              ) -> dict[str, Any]:
    """Run the five L-branch evaluations and assemble the T16 payload.

    :param decl: Declaration summary from the dispatch.
    :param engagement_id: Engagement identifier.
    :param modality: Verified modality (agentic adds a trajectory audit).
    :param trace_sample: Resolved ``trace_sample_uri`` content (agentic only);
        caller resolves it (needs the evidence store) via
        :func:`aaa.agents.tier3.uagf_tam_l.trace_sample.resolve_trace_sample`.
    :param declared_controls: What the client's guardrail configuration and RAG
        manifest state, from
        :func:`aaa.agents.tier3.uagf_tam_l.declared_controls.resolve_declared_controls`.
        Both documents were collected and gated on but never read until
        2026-09-11; a control the client declares as *not implemented* is
        evidence the audit must carry, not a gap to infer.
    :param ragas_metrics: RAGAs results already measured by the caller within its
        phase budget; measured here, unbounded, when omitted.
    :returns: The T16 evidence payload.
    """
    golden_set = run_golden_set(questions, answers, expected)
    if ragas_metrics is None:  # the branch measures it within its budget (T-20260914-013)
        ragas_metrics = ragas_eval(questions, contexts, answers, expected)
    groundedness = groundedness_check(
        context=" ".join(contexts[0]) if contexts else None,
        answer=answers[0] if answers else None)
    injection_results = prompt_injection_suite(
        target_uri=decl.get("stage_c", {}).get("read_only_api_endpoint"),
        system_prompt=decl.get("system_prompt_text"))
    trajectory = None
    if modality == "agentic":
        trajectory = trajectory_audit(
            trace_sample or [],
            decl.get("stage_b", {}).get("tool_inventory", []))
    return {
        "engagement_id": engagement_id,
        "golden_set_results": golden_set,
        "ragas_metrics": ragas_metrics,
        "groundedness_metrics": groundedness,
        "prompt_injection_results": injection_results,
        "declared_controls": declared_controls,
        "trajectory_audit": trajectory,
        "overall_verdict": derive_verdict(
            golden_set, ragas_metrics, injection_results,
            {**(decl.get("stage_b", {}).get("accuracy_metrics") or {}),
             **(decl.get("stage_b", {}).get("robustness_metrics") or {})}),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
