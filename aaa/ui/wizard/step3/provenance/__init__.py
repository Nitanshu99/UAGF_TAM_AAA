"""Model-provenance inputs for the L-branch (LLM / agentic) Stage B form.

Shown only for generative modalities, alongside the other LLM-only fields.
A tabular customer uploads a model file and is done; an LLM customer usually
runs weights they do not own — a vendor endpoint, or a base model plus an
adapter — and the rest of Stage B has nowhere to say so. Without these
questions the dossier can only describe a model as a file we hold, which is
how a case came to declare ``huggingface`` / ``transformers`` while supplying
no artefact at all.
"""
from __future__ import annotations

import streamlit as st

from aaa.platform.state.model_vocab import ACCESS_MODES, MODEL_PROVIDERS, REFERENCE_MODES
from aaa.ui.wizard.step3.provenance.fields import render_question
from aaa.ui.wizard.step3.provenance.vendors import pin_for, questions_for

#: Stage A modalities that route to the L-branch.
_LLM_MODALITIES = frozenset({"llm", "agentic", "gpai"})

#: Plain-English gloss for each access mode, shown under the selector.
_MODE_HELP = (
    "How the auditor obtains a runnable model. 'artifact_upload' — you upload the "
    "weights. 'registry_reference' — we pull them from a registry at a pinned "
    "revision. 'base_plus_adapter' — a base model plus your fine-tuned adapter. "
    "'hosted_api' — no weights exist to share; evaluation calls your vendor "
    "endpoint. 'not_provided' — no runnable model, so the audit is limited to "
    "documents and traces, and the report will say so."
)


def is_llm_branch() -> bool:
    """True when the declared modality routes to the L-branch.

    :returns: Whether provenance questions apply to this engagement.
    :rtype: bool
    """
    return str(st.session_state.get("s3_a_declared_modality") or "") in _LLM_MODALITIES


def render_provenance() -> None:
    """Render the access-mode selector and, when needed, the vendor branch."""
    if not is_llm_branch():
        return
    st.markdown("#### Model provenance (LLM / agentic)")
    st.caption(
        "Tells the auditor which model to evaluate and how to reach it (Art. 11). "
        "We never host your weights — we record what identifies them."
    )
    st.selectbox("How is the model made available?", options=("", *ACCESS_MODES),
                 key="s3_b_access_mode", help=_MODE_HELP)
    if st.session_state.get("s3_b_access_mode") not in REFERENCE_MODES:
        return
    st.selectbox("Model provider", options=("", *MODEL_PROVIDERS),
                 key="s3_b_ref_provider",
                 help="The vendor or registry serving the model, not your internal name for it.")
    provider = str(st.session_state.get("s3_b_ref_provider") or "")
    if not provider:
        st.info("Select a provider to see the details we need to identify the exact model.")
        return
    st.caption(f"Version pin for {provider}: **{pin_for(provider)}**")
    for reference_key, label, help_text in questions_for(provider):
        render_question(reference_key, label, help_text)
