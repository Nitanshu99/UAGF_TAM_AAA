#!/usr/bin/env python3
"""
smoke_group7.py — Smoke test for Group 7 (Phase 4 Output Fairness Tester).

Instantiates OutputFairnessTester directly (bypassing the full orchestrator)
and validates:
  1. All five tools execute without errors.
  2. T12 and T13 artefacts are stored in the EvidenceStore.
  3. T12 and T13 payloads satisfy their JSON-Schema (draft-07) constraints.
  4. Overall verdict and sampling-log fields are present and consistent.

Run from the repository root:
    python scripts/smoke_group7.py

Exit code 0 = all assertions passed.
Exit code 1 = one or more checks failed.
"""
from __future__ import annotations

import asyncio
import json
import pathlib
import sys

# ---------------------------------------------------------------------------
# Add repo root to sys.path so local imports resolve without install.
# ---------------------------------------------------------------------------
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.agents.base import Dispatch
from src.agents.tier2.output_fairness import OutputFairnessTester
from src.platform.evidence import EvidenceStore


# ---------------------------------------------------------------------------
# Synthetic fixture: small binary-classification dataset (tabular).
# Sensitive feature: "group" (0 = group A, 1 = group B).
# Deliberately skewed so fairness metrics return non-trivial verdicts.
# ---------------------------------------------------------------------------
_Y_TRUE       = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0,   # 10 rows
                 1, 1, 0, 0, 1, 1, 0, 0, 1, 0]    # 10 more
_Y_PRED       = [1, 0, 1, 0, 1, 0, 1, 0, 0, 0,
                 1, 1, 0, 0, 1, 0, 0, 0, 1, 0]
_SENS         = ["A", "A", "A", "A", "A", "A", "A", "A", "A", "A",
                 "B", "B", "B", "B", "B", "B", "B", "B", "B", "B"]
_TEXTS        = [f"Prediction text for record {i}." for i in range(20)]
_PRED_IDS     = [str(i) for i in range(20)]
_ENGAGEMENT   = "smoke-group7-001"
_MODALITY     = "tabular"


def _load_schema(name: str) -> dict:
    """Load a JSON-Schema file from src/templates/."""
    path = REPO_ROOT / "src" / "templates" / f"{name}.json"
    with path.open() as fh:
        return json.load(fh)


def _validate_schema(instance: dict, schema: dict, label: str) -> list[str]:
    """Validate *instance* against *schema* using jsonschema if available."""
    errors: list[str] = []
    try:
        import jsonschema  # type: ignore
        try:
            jsonschema.validate(instance, schema)
        except jsonschema.ValidationError as exc:
            errors.append(f"{label}: schema violation — {exc.message}")
    except ImportError:
        # jsonschema not installed; skip schema validation but note it.
        print(f"  [WARN] jsonschema not installed — skipping schema validation for {label}.")
    return errors


async def _run() -> int:
    """Execute the smoke test; return exit code."""
    store = EvidenceStore()
    agent = OutputFairnessTester(evidence_store=store)

    dispatch = Dispatch(
        phase_id="P4",
        task_brief="Smoke-test run of Phase 4 OutputFairnessTester.",
        evidence_uris=[],
        output_contract="T12_output_fairness_report",
        declaration_summary={
            "engagement_id": _ENGAGEMENT,
            "modality": _MODALITY,
            "y_true": _Y_TRUE,
            "y_pred": _Y_PRED,
            "sensitive_features": _SENS,
            "sensitive_feature_names": ["group"],
            "privileged_group": "A",
            "positive_label": 1,
            "prediction_texts": _TEXTS,
            "prediction_ids": _PRED_IDS,
            "sampling_strategy": "first_n",
        },
    )

    print("Running OutputFairnessTester.process() ...")
    report = await agent.process(dispatch)
    print(f"  summary : {report.get('summary')}")
    print(f"  confidence : {report.get('confidence')}")

    failures: list[str] = []

    # ── 1. Report structure ───────────────────────────────────────────────
    for field in ("phase_id", "artefact_uri", "summary", "confidence",
                  "tool_calls", "declaration_verification_delta"):
        if field not in report:
            failures.append(f"Report missing field '{field}'")

    delta = report.get("declaration_verification_delta", {})
    artefacts = delta.get("phase_artefacts", {})

    for tid in ("T12_output_fairness_report", "T13_output_sampling_log"):
        if tid not in artefacts:
            failures.append(f"delta.phase_artefacts missing '{tid}'")

    # ── 2. Artefacts stored in EvidenceStore ─────────────────────────────
    index = store.get_index(_ENGAGEMENT)
    stored_types = {e["artefact_type"] for e in index}
    for tid in ("T12_output_fairness_report", "T13_output_sampling_log"):
        if tid not in stored_types:
            failures.append(f"EvidenceStore missing artefact '{tid}'")

    # Retrieve stored artefacts for schema validation
    t12_uri = artefacts.get("T12_output_fairness_report", {}).get("uri", "")
    t13_uri = artefacts.get("T13_output_sampling_log", {}).get("uri", "")
    t12 = store.get_artefact(t12_uri) or {}
    t13 = store.get_artefact(t13_uri) or {}

    # ── 3. Schema validation ──────────────────────────────────────────────
    failures += _validate_schema(t12, _load_schema("T12_output_fairness_report"), "T12")
    failures += _validate_schema(t13, _load_schema("T13_output_sampling_log"), "T13")

    # ── 4. Semantic sanity checks ─────────────────────────────────────────
    _VALID_VERDICTS = {"PASS", "PASS_WITH_OBSERVATIONS", "FAIL", "NOT_TESTED"}

    for metric in ("demographic_parity", "equal_opportunity",
                   "disparate_impact", "subgroup_metrics"):
        v = t12.get(metric, {}).get("verdict")
        if v not in _VALID_VERDICTS:
            failures.append(f"T12.{metric}.verdict invalid: {v!r}")

    if t12.get("overall_fairness_verdict") not in _VALID_VERDICTS:
        failures.append(f"T12.overall_fairness_verdict invalid: {t12.get('overall_fairness_verdict')!r}")

    if t13.get("overall_verdict") not in _VALID_VERDICTS:
        failures.append(f"T13.overall_verdict invalid: {t13.get('overall_verdict')!r}")

    if t13.get("sample_size", -1) < 0:
        failures.append("T13.sample_size must be >= 0")

    tox = t13.get("toxicity_results", {})
    if tox.get("verdict") not in _VALID_VERDICTS:
        failures.append(f"T13.toxicity_results.verdict invalid: {tox.get('verdict')!r}")

    # ── 5. Tool call trace ────────────────────────────────────────────────
    tool_names = {tc["tool"] for tc in report.get("tool_calls", [])}
    for expected in ("demographic_parity", "equal_opportunity",
                     "disparate_impact", "subgroup_metrics", "toxicity_classifier"):
        if expected not in tool_names:
            failures.append(f"tool_calls missing '{expected}'")

    # ── Summary ───────────────────────────────────────────────────────────
    print()
    if failures:
        print(f"FAILED — {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  ✗ {f}")
        return 1
    else:
        print("PASSED — all checks passed ✓")
        print(f"  T12 overall_fairness_verdict : {t12.get('overall_fairness_verdict')}")
        print(f"  T13 overall_verdict           : {t13.get('overall_verdict')}")
        print(f"  T13 sample_size               : {t13.get('sample_size')}")
        print(f"  Toxicity flagged              : {tox.get('flagged_count', 0)}/{tox.get('sample_size', 0)}")
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_run()))
