"""Final Report assembly for Phase 3."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import Report
from aaa.agents.tier2.model_validator.context import Explainability, LlmSynthesis


def primary_metric_str(metrics_result: dict[str, Any]) -> str:
    """Format the primary metric as ``name=value`` (or ``name=n/a``).

    :param metrics_result: Output of ``metric_suite``.
    :returns: Human-readable primary-metric string.
    """
    value = metrics_result.get("primary_metric_value")
    if isinstance(value, (int, float)):
        return f"{metrics_result.get('primary_metric')}={value:.3f}"
    return f"{metrics_result.get('primary_metric')}=n/a"


def assemble_report(uris: dict[str, str], delta: dict[str, Any],
                    metrics_result: dict[str, Any], expl: Explainability,
                    robustness_result: dict[str, Any], llm: LlmSynthesis) -> Report:
    """Build the Phase 3 :class:`~aaa.agents.base.Report`.

    :param uris: Stored artefact URIs keyed by template id.
    :param delta: Assembled ``declaration_verification_delta``.
    :param metrics_result: Output of ``metric_suite``.
    :param expl: Explainability evidence from step 3.
    :param robustness_result: Output of ``robustness_probe``.
    :param llm: LLM synthesis outcome.
    :returns: Report with summary, confidence and tool-call log.
    """
    verdict = robustness_result.get("overall_robustness_verdict", "NOT_TESTED")
    hitl_required = bool(delta.get("hitl_required"))
    primary = primary_metric_str(metrics_result)
    return Report(
        phase_id="P3",
        artefact_uri=uris["T09_model_card"],
        summary=(llm.summary
                 or f"Phase 3 complete. {primary}, "
                    f"explainability={','.join(expl.techniques)}, "
                    f"robustness={verdict}."),
        confidence=0.6 if hitl_required else 0.85,
        tool_calls=[
            {"tool": "metric_suite",
             "result": f"{metrics_result.get('metric_suite_tool')}: {primary}"},
            {"tool": "explainability",
             "result": f"techniques={expl.techniques}, "
                       f"global_features={len(expl.global_expl.get('feature_importance', []))}, "
                       f"local_instances={len(expl.local_expl)}, "
                       f"visual_maps={len(expl.visual_expl)}"},
            {"tool": "robustness_probe",
             "result": f"verdict={verdict}, "
                       f"probes={len(robustness_result.get('probes', []))}"},
            {"tool": "client_doc_search", "result": f"hits={len(llm.client_doc_hits)}"},
            {"tool": "prompt_runtime", "result": llm.prompt_note},
        ],
        declaration_verification_delta=delta,
    )
