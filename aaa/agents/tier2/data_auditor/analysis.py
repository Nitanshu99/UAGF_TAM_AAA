"""Deterministic Phase 2 analysis: dataset tools, verdict, and findings."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.data_auditor.bias import examine_label_bias, label_bias_fails
from aaa.agents.tier2.data_auditor.dataset import dataset_uri_of
from aaa.agents.tier2.data_auditor.drift import run_drift
from aaa.agents.tier2.data_auditor.resolve import resolve_dataframe
from aaa.agents.tier2.data_auditor.t06.measured import measure
from aaa.agents.tier2.data_auditor.verdict import apply_verdict
from aaa.tools.class_balance import class_balance
from aaa.tools.data_profile import data_profile, not_profiled
from aaa.tools.missingness_scan import missingness_scan
from aaa.tools.pii_scan import pii_scan


def run_analysis(agent: Any, t01b: dict, decl: dict) -> dict[str, Any]:
    """Run the full deterministic Phase 2 analysis; returns the context.

    Loads the real dataset, runs the four data tools, derives the quality
    verdict, and collects the findings and insufficient-evidence articles.
    """
    stage_b: dict[str, Any] = decl.get("stage_b") or {}
    target_col: str | None = decl.get("target_column")
    findings: list[dict[str, Any]] = []
    insufficient: set[str] = set()

    df, data_available, target_col = resolve_dataframe(
        agent, t01b, decl, stage_b, target_col, findings)
    # The stand-in frame is not the dataset: its zero counts are not a profile.
    profile_result = data_profile(df, target_column=target_col) if data_available else not_profiled()
    miss_result = missingness_scan(df)
    balance_result = class_balance(df, target_column=target_col)
    pii_result = pii_scan(df)
    drift_result = run_drift(agent.store, t01b, decl, findings)

    declared_special_cat = bool(decl.get("special_category_data", False))
    special_cat_delta = bool(pii_result.get("special_category_data_detected")) and not declared_special_cat
    label_bias = examine_label_bias(df, data_available, decl, target_col, findings)

    verdict = apply_verdict(data_available, stage_b or t01b, profile_result,
                            miss_result, balance_result, pii_result,
                            findings, insufficient, special_cat_delta)
    # PASS beside a possibly-material label-bias finding contradicted itself, and the
    # Verifier held T07 for it (case 01, 2026-09-13): the finding is an observation.
    if verdict == "PASS" and label_bias_fails(label_bias):
        verdict = "PASS_WITH_OBSERVATIONS"
    return {
        "profile_result": profile_result, "miss_result": miss_result,
        "balance_result": balance_result, "pii_result": pii_result,
        "drift_result": drift_result,
        "verdict": verdict, "findings": findings, "insufficient": insufficient,
        "special_cat_delta": special_cat_delta,
        "effective_special_cat": declared_special_cat or bool(
            pii_result.get("special_category_data_detected", False)),
        "label_bias": label_bias,
        "measurement": measure(df, data_available, dataset_uri_of(t01b, decl), miss_result),
    }
