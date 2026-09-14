"""Technical-documentation inventory panel for the results page."""
from __future__ import annotations

import html

import streamlit as st

from aaa.ui import styles

#: stage_b URI field → customer-facing label (mirrors the PDF dossier section)
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


def render_dossier(final: dict) -> None:
    """Render the Annex IV documentation inventory from the client submission.

    :param final: Final ``AuditState`` dictionary.
    :type final: dict
    """
    stage_b = (final.get("client_submission") or {}).get("stage_b") or {}
    if not stage_b:
        return
    provided = sum(1 for field in _DOC_FIELDS if stage_b.get(field))
    styles.section_title(
        "Technical documentation",
        f"Annex IV artefacts submitted with this engagement ({provided}/{len(_DOC_FIELDS)}).")
    rows = "".join(
        f"<tr><td>{html.escape(label)}</td>"
        + ('<td><span class="aaa-pill is-ok">provided</span></td>'
           if stage_b.get(field)
           else '<td><span class="aaa-pill is-none">not provided</span></td>')
        + "</tr>"
        for field, label in _DOC_FIELDS.items())
    st.markdown('<div class="aaa-card aaa-scroll-x"><table class="aaa-matrix">'
                f"<tbody>{rows}</tbody></table></div>", unsafe_allow_html=True)
    if stage_b.get("task_type"):
        st.caption(f"Declared model metadata: task `{stage_b['task_type']}` · format "
                   f"`{stage_b.get('model_format') or '—'}` · framework "
                   f"`{stage_b.get('model_framework') or '—'}`")
