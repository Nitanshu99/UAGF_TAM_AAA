"""Stage B payload collector (reads wizard widget session state)."""
from __future__ import annotations

from typing import Any

import streamlit as st

from aaa.ui.wizard.collect.stage.b_meta import data_dictionary_block, model_meta_fields
from aaa.ui.wizard.constants import DOC_UPLOAD_FIELDS, OPTIONAL_UPLOAD_FIELDS
from aaa.ui.wizard.listing import split_items
from aaa.ui.wizard.parsing import parse_stage_b_metrics


def collect_stage_b() -> dict:
    """Assemble the Stage B technical-documentation payload from session state.

    :returns: Stage B dictionary matching the T01b (Annex IV) schema.
    """
    s = st.session_state
    accuracy, robustness = parse_stage_b_metrics(s.get("s3_b_accuracy_metrics_raw") or "{}")
    result: dict[str, Any] = {
        key: s.get(f"s3_b_{key}", "")
        for key in ("general_description", "model_type", "design_process",
                    "training_data_description", "data_governance_measures",
                    "monitoring_measures", "logging_capabilities")
    }
    result["accuracy_metrics"] = accuracy
    result["lifecycle_change_log"] = [
        ln for ln in s.get("s3_b_lifecycle_change_log_raw", "").splitlines() if ln.strip()]
    result["harmonised_standards"] = split_items(s.get("s3_b_harmonised_standards_raw", ""))
    result["other_standards"] = split_items(s.get("s3_b_other_standards_raw", ""))
    result["tool_inventory"] = split_items(s.get("s3_b_tool_inventory_raw", ""))
    if robustness is not None:
        result["robustness_metrics"] = robustness
    result.update(model_meta_fields(s))
    dd_block = data_dictionary_block(s)
    if dd_block:
        result["data_dictionary"] = dd_block
    for key in {**DOC_UPLOAD_FIELDS, **OPTIONAL_UPLOAD_FIELDS}:
        uri = (s.get("s3_b_uris") or {}).get(key)
        if uri:
            result[key] = uri
    return result
