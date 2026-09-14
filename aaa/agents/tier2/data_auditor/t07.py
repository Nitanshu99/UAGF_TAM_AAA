"""T07 Data Quality Report assembly from tool outputs."""
from __future__ import annotations

from typing import Any

from aaa.tools.findings.measured import measured

#: PSI bands ``drift_test`` reports; the T07 schema wants one method name.
_METHOD = "population_stability_index"


def _drift_block(drift_result: dict[str, Any] | None,
                 reference_uri: str | None) -> dict[str, Any]:
    """Render ``drift_test`` output into the T07 ``drift`` block.

    The block was hardcoded to nulls while ``run_drift`` computed a real result
    (F10): Art. 10 §2(g) was measured on every Phase 2 run and recorded
    nowhere. A result that could not be computed still says so here — "not
    measured" and "measured, no drift" are different findings.

    :param drift_result: Output of ``aaa.tools.drift_test.drift_test``.
    :type drift_result: dict[str, Any] | None
    :param reference_uri: URI of the reference (training) dataset, if known.
    :type reference_uri: str | None
    :returns: The T07 ``drift`` block.
    :rtype: dict[str, Any]
    """
    result = drift_result or {}
    if not result.get("computed"):
        return {"reference_dataset_uri": reference_uri, "drift_detected": None,
                "drifted_columns": [], "drift_share": None, "test_method": None}
    scored = [f for f in result.get("features", []) if f.get("psi") is not None]
    drifted = list(result.get("drifted_features", []))
    return {
        "reference_dataset_uri": reference_uri,
        "drift_detected": bool(drifted),
        "drifted_columns": drifted,
        "drift_share": round(len(drifted) / len(scored), 4) if scored else None,
        "test_method": _METHOD,
    }


def _opening(miss_result: dict, balance_result: dict, pii_result: dict) -> str:
    """What the tools did, never "assessed" beside results that are all unmeasured.

    Case 04 (no dataset) read "Data quality assessed via automated tools." above a
    column of "not measured" (T-20260914-012).
    """
    if any(v is not None for v in (miss_result.get("overall_missingness_pct"),
                                   balance_result.get("imbalance_severity"),
                                   pii_result.get("pii_detected"))):
        return ("Data quality measured on the supplied dataset: completeness and "
                "representativeness (Art. 10(3)) and the bias examination of Art. 10(2)(f).")
    return ("No dataset was loaded, so no data-quality tool measured anything and the "
            "Art. 10(2)(f) and Art. 10(3) examination of the data was not performed.")


def build_t07(engagement_id: str, profile_result: dict, miss_result: dict,
              balance_result: dict, pii_result: dict, verdict: str, now: str,
              drift_result: dict | None = None,
              reference_uri: str | None = None, label_bias: dict | None = None,
              declared_size: str = "") -> dict:
    """Build the T07 Data Quality Report.

    :param engagement_id: Engagement identifier.
    :param profile_result: ``data_profile`` output.
    :param miss_result: ``missingness_scan`` output.
    :param balance_result: ``class_balance`` output.
    :param pii_result: ``pii_scan`` output.
    :param verdict: Overall quality verdict.
    :param now: ISO-8601 generation timestamp.
    :param drift_result: Output of ``drift_test`` (Art. 10 §2(g)).
    :param reference_uri: Training-dataset URI the drift test compared against.
    :param label_bias: ``label_disparity`` output (Art. 10 §2(f)), when run.
    :param declared_size: The declared-vs-supplied count sentence, when the file examined
        is the declared training set and its counts differ from the declaration.
    :returns: The T07 payload matching the template schema.
    """
    return {
        "engagement_id": engagement_id,
        "dataset_summary": profile_result,
        "missingness": miss_result,
        "class_balance": balance_result,
        "drift": _drift_block(drift_result, reference_uri),
        "label_bias": label_bias,
        "pii_scan": pii_result,
        "overall_quality_verdict": verdict,
        "quality_narrative": (
            f"{_opening(miss_result, balance_result, pii_result)} "
            f"Missingness overall: {measured(miss_result.get('overall_missingness_pct'), '.1f', '%')}. "
            f"Class imbalance: {measured(balance_result.get('imbalance_severity'))}. "
            f"PII detected: {measured(pii_result.get('pii_detected'))}. "
            f"Overall verdict: {verdict}.{declared_size}"
        ),
        "generated_at": now,
    }
