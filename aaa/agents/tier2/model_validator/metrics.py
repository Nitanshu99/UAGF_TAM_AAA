"""Declaration diff of declared vs independently-computed metrics."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.model_validator.corroboration import judged
from aaa.agents.tier2.model_validator.targets import check_targets
from aaa.tools.findings import make_finding, make_positive_finding

#: Declared key → (computed metrics key, human label). A declared ``f1_score`` is the
#: positive-class F1 (scikit-learn's default), so it is compared with ``f1``, not
#: ``f1_macro`` (T-20260913-069).
METRIC_MAP = {
    "accuracy": ("accuracy", "accuracy"),
    "auc_roc": ("roc_auc", "AUC-ROC"),
    "f1_score": ("f1", "F1"),
    "precision": ("precision", "precision"),
    "recall": ("recall", "recall"),
}


def diff_declared_metrics(
    declared: dict[str, Any],
    metrics_result: dict[str, Any],
    intervals: dict[str, tuple[float, float]] | None = None,
    mapping: dict[str, tuple[str, str]] | None = None,
    targets: bool = True,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Compare declared performance metrics with the re-computed ones.

    A declared figure inside the measured metric's 95% bootstrap interval is
    corroborated; above it the declaration overstates the system (material); below
    it, understates it. The interval, not a fixed gap, decides — the fixed 0.05 /
    0.10 tolerances and the AUC >= 0.95 leakage flag ignored how many rows the
    measurement rests on (T-20260914-002).

    :param declared: ``accuracy_metrics`` block from the Stage B dossier.
    :param metrics_result: Output of ``metric_suite``.
    :param intervals: :func:`aaa.tools.metric_suite.interval.bootstrap_intervals`.
    :param mapping: Declared key → (computed key, label); :data:`METRIC_MAP` by default.
    :param targets: Whether to check declared error-rate targets too (once per phase).
    :returns: ``(findings, positive_findings)`` lists.
    """
    findings: list[dict[str, Any]] = []
    positives: list[dict[str, Any]] = []
    computed = metrics_result.get("metrics", {}) or {}
    for decl_key, (comp_key, label) in (METRIC_MAP if mapping is None else mapping).items():
        decl_val, comp_val = declared.get(decl_key), computed.get(comp_key)
        if not isinstance(decl_val, (int, float)) or not isinstance(comp_val, (int, float)):
            continue
        materiality, note = judged(label, float(decl_val), float(comp_val),
                                    (intervals or {}).get(comp_key))
        fid = f"P3-METRIC-{comp_key.upper()}"
        if materiality is None:
            positives.append(make_positive_finding(
                finding_id=fid, description=note, articles=["Art.15"], source_phase="P3"))
        elif materiality:
            findings.append(make_finding(
                finding_id=fid, description=note, materiality=materiality,
                articles=["Art.15"], source_phase="P3",
                recommendation="Reconcile the declared metric with an audited evaluation protocol.",
                declared=float(decl_val), observed=float(comp_val)))
    if not targets:
        return findings, positives
    target_findings, target_positives = check_targets(declared, computed,
                                                      metrics_result.get("confusion"))
    return findings + target_findings, positives + target_positives
