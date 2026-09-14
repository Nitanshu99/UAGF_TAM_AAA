"""Technical-documentation inventory section for the customer-facing PDF."""
from __future__ import annotations

from typing import Any

from reportlab.platypus import Paragraph

from aaa.tools.report_render.pdf.elements import keep_section, section
from aaa.tools.report_render.pdf.tables import kv_table
from aaa.tools.report_render.pdf.theme import GREEN, MUTED, STYLES

#: stage_b URI field → customer-facing label
_DOC_FIELDS = {
    "risk_management_file_uri": "Risk management documentation (Art. 9)",
    "eu_doc_uri": "EU Declaration of Conformity",
    "post_market_plan_uri": "Post-market monitoring plan (Art. 72)",
    "training_dataset_uri": "Training dataset",
    "evaluation_dataset_uri": "Evaluation dataset",
    "model_artifact_uri": "Model artefact",
    "system_prompt_uri": "System prompt (LLM/agentic)",
    "rag_manifest_uri": "RAG manifest (LLM/agentic)",
    "guardrail_config_uri": "Guardrail configuration (LLM/agentic)",
    "golden_set_uri": "Golden evaluation set (LLM/agentic)",
}


def build_dossier(state: dict[str, Any]) -> list[Any]:
    """Build the Annex IV documentation inventory from the client submission.

    :param state: The audit state (``client_submission.stage_b``).
    :type state: dict[str, Any]
    :returns: Section flowables (empty when no submission is present).
    :rtype: list[Any]
    """
    stage_b = (state.get("client_submission") or {}).get("stage_b") or {}
    if not stage_b:
        return []
    provided = sum(1 for f in _DOC_FIELDS if stage_b.get(f))
    rows = []
    for field, label in _DOC_FIELDS.items():
        mark = (f'<font color="{GREEN.hexval()}"><b>provided</b></font>'
                if stage_b.get(field)
                else f'<font color="{MUTED.hexval()}">not provided</font>')
        rows.append((label, mark))
    flow = section("Technical documentation inventory",
                   f"Annex IV artefacts submitted with this engagement "
                   f"({provided}/{len(_DOC_FIELDS)} provided).")
    flow.append(kv_table(rows))
    if stage_b.get("task_type"):
        flow.append(Paragraph(
            f"Declared model metadata: task {stage_b['task_type']}, format "
            f"{stage_b.get('model_format') or '—'}, framework "
            f"{stage_b.get('model_framework') or '—'}.", STYLES["muted"]))
    return keep_section(flow)
