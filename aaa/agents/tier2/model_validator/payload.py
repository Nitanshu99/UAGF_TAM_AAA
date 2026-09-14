"""The Phase 3 prompt payload: the declaration, the retrieved evidence, the tool outputs."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.tools_run import tools_run


def phase3_payload(message: dict[str, Any], decl: dict[str, Any],
                   client_doc_hits: list, regulatory_hits: list,
                   metrics_result: dict[str, Any], expl: Any,
                   robustness_result: dict[str, Any]) -> dict[str, Any]:
    """Assemble what the Phase 3 synthesis call is given.

    :param message: The dispatch.
    :param decl: The declaration summary.
    :param client_doc_hits: Seeded client-document hits.
    :param regulatory_hits: Seeded corpus hits.
    :param metrics_result: What the metrics tool computed.
    :param expl: The explainability result.
    :param robustness_result: What the robustness probe returned.
    :returns: The user payload.
    """
    return {
        "task": message.get("task_brief")
        or "Execute Phase 3 model validation per the Phase 3 Protocol.",
        "evidence_uris": message.get("evidence_uris", []),
        "declaration_summary": decl,
        "client_doc_hits": client_doc_hits,
        "regulatory_hits": regulatory_hits,
        "rerun_context": message.get("rerun_context"),
        "tool_outputs": {"metrics_result": metrics_result,
                         "techniques": expl.techniques,
                         "global_explanation": expl.global_expl,
                         "local_explanations": expl.local_expl[:5],
                         "visual_explanations": expl.visual_expl[:5],
                         # A tool that ran and fell back to a model-free proxy
                         # returns a well-formed result either way; without
                         # this the model cannot tell the two apart.
                         "explainability_degraded": expl.degraded,
                         "robustness_result": robustness_result},
        "tools_executed": tools_run("P3", client_docs=bool(client_doc_hits),
                                    techniques=expl.techniques),
    }


__all__ = ["phase3_payload"]
