"""Stage B supporting-document uploads and data-dictionary inputs."""
from __future__ import annotations

import streamlit as st

from aaa.platform.evidence import EvidenceStore
from aaa.ui.wizard.constants import DOC_UPLOAD_FIELDS, OPTIONAL_UPLOAD_FIELDS
from aaa.ui.wizard.step3.uploads.row import uploader_row

#: The three documents every system needs, whatever it is built from — they are
#: Annex IV §5, §8 and §9 and they carry 0.25 of the completeness gate between
#: them.
_CORE_DOCS = ("risk_management_file_uri", "eu_doc_uri", "post_market_plan_uri")

#: Asked for only when the system involves an LLM or agents. Shown, never
#: hidden: `component_modalities` says a system can be composite — a case can
#: declare `llm` while one of its two components is `nlp` — and the wizard only
#: ever sees the single scalar `declared_modality`. Hiding an uploader on that
#: basis would silently deny a composite system a document the audit needs, so
#: the section collapses instead, open when the scalar is in the L-branch.
_LLM_DOCS = ("system_prompt_uri", "rag_manifest_uri", "guardrail_config_uri",
             "golden_set_uri", "trace_sample_uri")
def _band(store: EvidenceStore, eid: str, keys: tuple[str, ...],
          fields: dict, *, note_existing: bool = True) -> None:
    """Render one labelled group of uploaders."""
    for key in keys:
        spec = fields.get(key)
        if spec is None:
            continue
        label, description, file_types = spec
        uploader_row(store, eid, key, label, description, file_types,
                     note_existing=note_existing)


def render_uploads(store: EvidenceStore, eid: str) -> None:
    """Render supporting-document and optional-artefact uploaders.

    Three bands rather than two flat lists of twelve: what every system needs,
    what a language-model or agentic system additionally needs, and what buys
    the audit real evidence instead of a declaration.

    :param store: Evidence store for persisted uploads.
    :param eid: Engagement identifier.
    """
    from aaa.ui.wizard.collect import collect_stage_a
    from aaa.ui.wizard.step3.uploads.intro import band_heading, uploads_footer

    band_heading("Required of every system",
                 "Annex IV §5, §8 and §9. Together these are worth a quarter of "
                 "the completeness score.")
    _band(store, eid, _CORE_DOCS, DOC_UPLOAD_FIELDS)

    modality = str(collect_stage_a().get("declared_modality") or "")
    is_l_branch = modality in {"llm", "agentic", "gpai"}
    with st.expander("If your system uses a language model or agents",
                     expanded=is_l_branch):
        st.caption(
            "Required when any part of your system is an LLM or an agent — "
            "including a system that is only partly one. Leave blank if none apply.")
        _band(store, eid, _LLM_DOCS, DOC_UPLOAD_FIELDS)

    band_heading("Model and data",
                 "Optional, and the single biggest lever on how much of the "
                 "audit is measured rather than taken on trust.")
    _band(store, eid, tuple(OPTIONAL_UPLOAD_FIELDS), OPTIONAL_UPLOAD_FIELDS)

    uploads_footer(len(st.session_state.get("s3_b_uris") or {}),
                   len(DOC_UPLOAD_FIELDS) + len(OPTIONAL_UPLOAD_FIELDS))


__all__ = ["render_uploads"]
