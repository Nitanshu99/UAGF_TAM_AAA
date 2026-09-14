"""Persist step-1 uploads and index them for the audit's retrieval."""
from __future__ import annotations

import streamlit as st

from aaa.platform.evidence import EvidenceStore
from aaa.ui.wizard.loaders import store_uploaded_file
from aaa.ui.wizard.pipeline import ingest_documents

#: Stage B URI fields a step-1 upload can satisfy outright. The model artefact
#: and the datasets are the same files step 3 asks for under
#: ``OPTIONAL_UPLOAD_FIELDS``; before this, a customer who supplied them here
#: had them indexed for retrieval and then silently *not* counted towards Stage
#: B, so the Art. 15 and fairness checks came back INSUFFICIENT_EVIDENCE unless
#: they happened to upload the identical file a second time.
_MODEL_FIELD = "model_artifact_uri"
_DATASET_FIELDS = ("training_dataset_uri", "evaluation_dataset_uri")

#: What the review form does not get any more. Kept as a shape rather than
#: deleted: the ``/extract-triage`` endpoint still returns a populated version
#: of it, so re-enabling pre-fill here is a one-line change, not a rebuild.
_NO_EXTRACTION = {
    "stage_a_partial": {}, "stage_b_partial": {}, "field_confidence": {},
    "field_sources": {}, "missing_fields": [], "extraction_status": "not_attempted",
}


def _claim_stage_b_uri(field: str, uri: str) -> None:
    """Record *uri* against a Stage B field, without overwriting a later upload."""
    uris = st.session_state.setdefault("s3_b_uris", {})
    uris.setdefault(field, uri)


def persist_and_extract(store: EvidenceStore, eid: str, doc_files, model_file, dataset_files) -> None:
    """Store uploads, index them, and advance to the questions step."""
    doc_uris: list[str] = []
    for f in (doc_files or []):
        uri = store_uploaded_file(store, eid, "technical_doc", f)
        if uri:
            doc_uris.append(uri)
    if model_file:
        uri = store_uploaded_file(store, eid, _MODEL_FIELD, model_file)
        if uri:
            doc_uris.append(uri)
            _claim_stage_b_uri(_MODEL_FIELD, uri)
    for field, f in zip(_DATASET_FIELDS, dataset_files or []):
        uri = store_uploaded_file(store, eid, field, f)
        if uri:
            doc_uris.append(uri)
            _claim_stage_b_uri(field, uri)
    st.session_state["step1_doc_uris"] = doc_uris
    if doc_uris:
        with st.spinner("Filing your documents…"):
            st.session_state["ingest_result"] = ingest_documents(eid, doc_uris, store)
    else:
        st.session_state["ingest_result"] = {"chunks_indexed": 0, "sources": [], "error": None}
    st.session_state["extraction_result"] = dict(_NO_EXTRACTION)
    st.session_state["step3_initialized"] = False
    st.session_state["step"] = 2
    st.rerun()
