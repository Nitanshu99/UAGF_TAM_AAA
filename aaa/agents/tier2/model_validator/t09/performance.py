"""The T09 ``performance_metrics`` block: measured values beside the declared ones."""
from __future__ import annotations

from typing import Any


def performance_section(t01b: dict[str, Any], metrics_result: dict[str, Any],
                        declared: dict[str, Any] | None = None,
                        reason: str | None = None) -> dict[str, Any]:
    """Build the T09 ``performance_metrics`` block from metric_suite output.

    :param t01b: T01b Annex IV dossier artefact.
    :param metrics_result: Output of ``metric_suite``.
    :param declared: :func:`~aaa.agents.tier2.model_validator.declared.declared_metrics`.
    :param reason: Why nothing was measured, when nothing was.
    :returns: Performance section dictionary; measured fields are ``None`` when
        nothing was measured.
    """
    return {
        # A metric is named only when it was measured; "not measured" once stood in
        # the name field and the reason stood nowhere in the card.
        "primary_metric": (metrics_result.get("primary_metric")
                           if metrics_result.get("primary_metric_value") is not None else None),
        "primary_metric_value": metrics_result.get("primary_metric_value"),
        "not_measured_reason": reason,
        "metrics": metrics_result.get("metrics", {}),
        "calibration_error": metrics_result.get("calibration_error"),
        "evaluation_dataset_description": (
            f"Declared evaluation set: {t01b['evaluation_dataset_uri']}"
            if t01b.get("evaluation_dataset_uri") else None),
        "evaluation_sample_size": metrics_result.get("evaluation_sample_size"),
        "metric_suite_tool": metrics_result.get("metric_suite_tool"),
        # The provider's own figures, unverified, beside the measured ones (F6).
        "declared_metrics": declared,
    }
