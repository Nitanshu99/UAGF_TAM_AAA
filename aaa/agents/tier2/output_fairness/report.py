"""Final Report assembly for Phase 4."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import Report
from aaa.agents.tier2.output_fairness.context import LlmSynthesis, SuiteResult


def assemble_report(suite: SuiteResult, tox_result: dict[str, Any],
                    uris: dict[str, str], delta: dict[str, Any],
                    llm: LlmSynthesis) -> Report:
    """Build the Phase 4 :class:`~aaa.agents.base.Report`.

    :param suite: Fairness suite result.
    :param tox_result: ``toxicity_classifier`` result.
    :param uris: Stored artefact URIs keyed by template id.
    :param delta: Assembled ``declaration_verification_delta``.
    :param llm: LLM synthesis outcome.
    :returns: Report with summary, confidence and tool-call log.
    """
    hitl_required = bool(delta.get("hitl_required"))
    return Report(
        phase_id="P4",
        artefact_uri=uris["T12_output_fairness_report"],
        summary=(llm.summary
                 or f"Phase 4 complete. fairness_verdict={suite.overall_verdict}, "
                    f"toxicity_flagged={tox_result.get('flagged_count', 0)} / "
                    f"{tox_result.get('sample_size', 0)}."),
        confidence=0.6 if hitl_required else 0.85,
        tool_calls=[
            {"tool": "demographic_parity",
             "result": f"verdict={suite.dp['verdict']}, "
                       f"difference={suite.dp.get('difference')}"},
            {"tool": "equal_opportunity",
             "result": f"verdict={suite.eo['verdict']}, "
                       f"difference={suite.eo.get('difference')}"},
            {"tool": "disparate_impact",
             "result": f"verdict={suite.di['verdict']}, ratio={suite.di.get('ratio')}"},
            {"tool": "subgroup_metrics",
             "result": f"verdict={suite.sg['verdict']}, "
                       f"accuracy_gap={suite.sg.get('accuracy_gap')}"},
            {"tool": "toxicity_classifier",
             "result": f"verdict={tox_result['verdict']}, "
                       f"flagged={tox_result.get('flagged_count', 0)}"},
            {"tool": "prompt_runtime", "result": llm.prompt_note},
        ],
        declaration_verification_delta=delta,
    )
