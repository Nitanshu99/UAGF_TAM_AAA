"""The Annex IV §4 performance-metrics field, and what it will not record."""
from __future__ import annotations

import json

import streamlit as st

from aaa.ui.wizard.metric_check import discarded_metrics
from aaa.ui.wizard.progress import field_caption


def render_metrics_field(confidence: dict, sources: dict, missing: list) -> None:
    """Render the metrics JSON input, its validity error and any metrics it drops."""
    st.text_area(
        "Performance metrics (JSON)", key="s3_b_accuracy_metrics_raw",
        help='Annex IV §4 — Key performance metrics as JSON. Accepted formats: 1) flat object with '
             'metric names as keys and numbers as values, e.g. {"accuracy": 0.78, "auc": 0.82, '
             '"f1": 0.71}; 2) wrapped block with nested "accuracy_metrics" and "robustness_metrics", '
             'e.g. {"accuracy_metrics": {"accuracy": 0.78}, "robustness_metrics": {"psi": 0.04}}. '
             "All metric values must be numbers.",
        placeholder='{"accuracy": 0.78, "auc": 0.82, "f1": 0.71}', height=70)
    field_caption("accuracy_metrics", confidence, sources, missing)
    raw_metrics = st.session_state.get("s3_b_accuracy_metrics_raw", "{}")
    try:
        json.loads(raw_metrics)
    except json.JSONDecodeError:
        st.error("Performance metrics must be valid JSON.")
    if dropped := discarded_metrics(raw_metrics):
        st.warning("Not recorded as accuracy metrics (not a number between 0 and 1): "
                   f"{', '.join(dropped)}. Put operational figures such as latency under "
                   '"robustness_metrics" in the wrapped format.')


__all__ = ["render_metrics_field"]
