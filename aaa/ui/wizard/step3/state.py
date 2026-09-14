"""Session-state initialisation for wizard step 3 (first arrival only)."""
from __future__ import annotations

import json

import streamlit as st

from aaa.ui.wizard.constants import ANNEX_III_LABELS
from aaa.ui.wizard.loaders import init_key
from aaa.ui.wizard.step3.defaults import ADVANCED_A, EXTRACTED_A, EXTRACTED_B, QUESTIONNAIRE_A


def _as_text(value, joiner: str) -> str:
    """Coerce an extracted string-or-list value to widget text."""
    if isinstance(value, str):
        return value
    return joiner.join(value) if isinstance(value, list) else ""


def initialise_step3_state(extraction: dict, questionnaire: dict) -> None:
    """Pre-populate widget keys from extraction + questionnaire once.

    :param extraction: ``DocExtractionResult`` from step 1.
    :param questionnaire: Answers captured in step 2.
    """
    # M28: this used to return early on `step3_initialized`, on the assumption
    # that the `s3_*` widget keys it seeded would still be there. Streamlit drops
    # a widget's key when that widget stops rendering, so stepping forward to the
    # results screen deletes every one of them — and coming back (from a failed
    # intake validation, say, which is exactly when a customer comes back) found
    # the flag set, skipped re-seeding, and rendered the whole form empty while
    # the captions underneath still read "Auto-filled · 95% high confidence".
    # 95 % completeness became 35 % and the customer's work was gone.
    #
    # `init_key` only writes a key that is absent, so re-seeding on every entry
    # restores what Streamlit dropped and never overwrites a live edit. What the
    # customer last confirmed outranks the extraction it started from.
    confirmed_a = st.session_state.get("step4_stage_a") or {}
    confirmed_b = st.session_state.get("step4_stage_b") or {}
    # Company and system name were typed on the welcome screen. They outrank the
    # extractor's guess at the same two fields: the customer stated them about
    # themselves, and being shown a different company name than the one they
    # just entered is the kind of error that costs trust in everything below it.
    identity = st.session_state.get("intake_identity") or {}
    stage_a = {**extraction.get("stage_a_partial", {}),
               **{k: v for k, v in identity.items() if v}, **confirmed_a}
    stage_b = {**extraction.get("stage_b_partial", {}), **confirmed_b}
    for key, default in EXTRACTED_A.items():
        init_key(f"s3_a_{key}", stage_a.get(key, default))
    for key, default in QUESTIONNAIRE_A.items():
        init_key(f"s3_a_{key}", questionnaire.get(key, default))
    for key, default in ADVANCED_A.items():
        init_key(f"s3_a_{key}", default)
    init_key("_s3_annex_iii_labels", [
        ANNEX_III_LABELS[k]
        for k in st.session_state.get("s3_a_declared_annex_iii_sections", [])
        if k in ANNEX_III_LABELS
    ])
    for key in EXTRACTED_B:
        init_key(f"s3_b_{key}", stage_b.get(key, ""))
    # Nothing extracted means nothing declared: an empty object, never a sample
    # figure, which would be recorded as the provider's own Annex IV §4 claim.
    raw_metrics = stage_b.get("accuracy_metrics", "")
    init_key("s3_b_accuracy_metrics_raw",
             raw_metrics if isinstance(raw_metrics, str) and raw_metrics
             else json.dumps(raw_metrics) if isinstance(raw_metrics, dict) else "{}")
    init_key("s3_b_lifecycle_change_log_raw", _as_text(stage_b.get("lifecycle_change_log", ""), "\n"))
    init_key("s3_b_harmonised_standards_raw", _as_text(stage_b.get("harmonised_standards", ""), ", "))
    init_key("s3_b_other_standards_raw", _as_text(stage_b.get("other_standards", ""), ", "))
    init_key("s3_b_tool_inventory_raw", _as_text(stage_b.get("tool_inventory", ""), ", "))
    init_key("s3_b_uris", {})
    st.session_state["step3_initialized"] = True
