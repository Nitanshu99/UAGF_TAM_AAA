#!/usr/bin/env python3
"""
smoke_group11.py — End-to-end reference smoke test for Group 11.

Reference case study: a tabular credit scorer (UCI German Credit), declared
``risk_tier=high``, ``annex_iii_sections=["5"]``, ``deployment_context=b2b``.

The script drives the full audit pipeline:

    IntakeValidator (Stages A/B/C)
        → Orchestrator (Stage 0 → Plan → Phase 1 → Route →
                        Parallel Phases 2/3/4 → Phase 5 →
                        Compliance Matrix → HITL Checkpoint → Phase 6)
        → ReportArchitect outputs T17 + T18

and asserts:

  1. All 12 workflow stages executed (3 intake + 9 orchestrator nodes).
  2. KPI 0 ``intake_completeness_score`` ≥ 0.80 (gate).
  3. KPI 1 ``completeness_score`` is computed (≥ 0.75).
  4. KPI 2 ``regulatory_coverage_pct`` is computed (≥ 75 %).
  5. Final verdict ∈ {PASS, PASS_WITH_OBSERVATIONS, FAIL}.
  6. T17 + T18 schemas validate (draft-07).
  7. T17 rows for Art. 9, Art. 43 and Annex III are non-empty and carry a
     non-stub evidence URI traceable to phase_artefacts.

Run from the repository root::

    AAA_OFFLINE_MODE=true python scripts/smoke_group11.py

Exit code 0 = all assertions passed.
Exit code 1 = one or more checks failed.
"""
from __future__ import annotations

import asyncio
import json
import os
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("AAA_OFFLINE_MODE", "true")
os.environ.setdefault("CGSA_FIXTURE_DIR", str(REPO_ROOT / "scripts" / "fixtures" / "cgsa"))

from src.agents.base import IntakeDispatch  # noqa: E402
from src.agents.intake_validator import IntakeValidator  # noqa: E402
from src.agents.tier1.orchestrator import Orchestrator  # noqa: E402
from src.platform.evidence import EvidenceStore  # noqa: E402

_FIXTURE_DIR = REPO_ROOT / "scripts" / "fixtures" / "uci_german_credit"
_ENGAGEMENT = "eng-uci-german-credit-001"
_VALID_VERDICTS = {"PASS", "PASS_WITH_OBSERVATIONS", "FAIL"}
_REQUIRED_T17_ARTICLES = ("Art.9", "Art.43", "Annex_III")


def _load_json(path: pathlib.Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


def _validate_schema(instance: dict, schema: dict, label: str) -> list[str]:
    errs: list[str] = []
    try:
        import jsonschema  # type: ignore
        try:
            jsonschema.validate(instance, schema)
        except jsonschema.ValidationError as exc:
            errs.append(f"{label}: schema violation — {exc.message}")
    except ImportError:
        print(f"  [WARN] jsonschema not installed — skipping {label} schema check.")
    return errs


async def _run() -> int:
    store = EvidenceStore()

    # ── Stage 0 A/B/C — seed payloads into EvidenceStore via IntakeValidator ──
    stage_a = _load_json(_FIXTURE_DIR / "stage_a.json")
    stage_b = _load_json(_FIXTURE_DIR / "stage_b.json")
    stage_c = _load_json(_FIXTURE_DIR / "stage_c.json")

    stage_a_uri = store.store_artefact(_ENGAGEMENT, "stage_a_raw", "stage_a_raw",
                                       stage_a, "smoke_group11")
    stage_b_uri = store.store_artefact(_ENGAGEMENT, "stage_b_raw", "stage_b_raw",
                                       stage_b, "smoke_group11")
    stage_c_uri = store.store_artefact(_ENGAGEMENT, "stage_c_raw", "stage_c_raw",
                                       stage_c, "smoke_group11")

    intake = IntakeValidator(evidence_store=store)
    intake_dispatch: IntakeDispatch = {
        "engagement_id": _ENGAGEMENT,
        "stage_a_uri": stage_a_uri,
        "stage_b_uri": stage_b_uri,
        "stage_c_uri": stage_c_uri,
        "annex_iv_schema_version": "1.0.0",
    }

    print("Running IntakeValidator (Stage 0 A/B/C) ...")
    initial_state = await intake.process(intake_dispatch)
    print(f"  intake_completeness_score = {initial_state['intake_completeness_score']:.2f}")

    # ── Orchestrator full run ────────────────────────────────────────────────
    # Pass IntakeValidator's full state directly into orch.run() so that
    # the T01a/T01b/T01c phase_artefacts are preserved.
    print("Running Orchestrator (Plan → P1 → P2/3/4 → P5 → CM → HITL → P6) ...")
    orch = Orchestrator(evidence_store=store)
    final = await orch.run(dict(initial_state))

    failures: list[str] = []

    # ── 1. All 12 workflow stages executed ───────────────────────────────────
    # Stage 0 A/B/C ⇒ T01a, T01b, T01c.
    # P1 ⇒ T02–T05.  P2 ⇒ T06–T08.  P3 ⇒ T09–T11.  P4 ⇒ T12–T13.
    # P5 ⇒ T14–T15.  P6 ⇒ T17, T18.
    required_tids = [
        "T01a_stage_a_triage", "T01b_annex_iv_dossier", "T01c_intake_completeness_report",
        "T02_system_card", "T03_annex_iii_mapping",
        "T04_risk_tier_decision", "T05_art43_decision",
        "T06_datasheet_for_datasets", "T07_data_quality_report",
        "T08_special_category_data_log",
        "T09_model_card", "T10_explainability_report", "T11_robustness_report",
        "T12_output_fairness_report", "T13_output_sampling_log",
        "T14_governance_findings", "T15_monitoring_logging_review",
        "T17_compliance_matrix", "T18_audit_report",
    ]
    artefacts = final.get("phase_artefacts", {})
    for tid in required_tids:
        ref = artefacts.get(tid) or {}
        if not ref.get("uri"):
            failures.append(f"phase_artefacts missing '{tid}'")

    # ── 2. KPI 0 ─ intake_completeness_score ≥ 0.80 ──────────────────────────
    ics = final.get("intake_completeness_score") or 0.0
    if ics < 0.80:
        failures.append(f"KPI 0 intake_completeness_score={ics:.2f} < 0.80")

    # ── 3. KPI 1 ─ completeness_score computed (≥ 0.75) ──────────────────────
    cs = final.get("completeness_score")
    if cs is None:
        failures.append("KPI 1 completeness_score not computed")
    elif cs < 0.75:
        failures.append(f"KPI 1 completeness_score={cs:.2f} < 0.75 baseline")

    # ── 4. KPI 2 ─ regulatory_coverage_pct computed (≥ 75 %) ─────────────────
    rc = final.get("regulatory_coverage_pct")
    if rc is None:
        failures.append("KPI 2 regulatory_coverage_pct not computed")
    elif rc < 75.0:
        failures.append(f"KPI 2 regulatory_coverage_pct={rc:.1f} < 75.0 baseline")

    # ── 5. Final verdict ─────────────────────────────────────────────────────
    verdict = final.get("final_verdict")
    if verdict not in _VALID_VERDICTS:
        failures.append(f"final_verdict invalid: {verdict!r}")

    # ── 6. T17 + T18 schema validation ───────────────────────────────────────
    t17_uri = artefacts.get("T17_compliance_matrix", {}).get("uri", "")
    t18_uri = artefacts.get("T18_audit_report", {}).get("uri", "")
    t17 = store.get_artefact(t17_uri) or {}
    t18 = store.get_artefact(t18_uri) or {}
    failures += _validate_schema(t17, _load_json(REPO_ROOT / "src/templates/T17_compliance_matrix.json"), "T17")
    failures += _validate_schema(t18, _load_json(REPO_ROOT / "src/templates/T18_audit_report.json"), "T18")

    # ── 7. Article traceability ─ Art.9, Art.43, Annex_III ────────────────
    t17_rows = {row.get("article"): row for row in (t17.get("articles") or [])}
    artefact_uris = {ref.get("uri") for ref in artefacts.values() if isinstance(ref, dict)}
    for art in _REQUIRED_T17_ARTICLES:
        row = t17_rows.get(art)
        if not row:
            failures.append(f"T17.articles missing '{art}'")
            continue
        evidence_uris = row.get("evidence_uris") or []
        if not evidence_uris:
            failures.append(f"T17.articles '{art}' has no evidence_uris")
            continue
        if not any(u in artefact_uris for u in evidence_uris):
            failures.append(
                f"T17.articles '{art}' evidence_uris not traceable to phase_artefacts: {evidence_uris}"
            )

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print(f"  intake_completeness_score : {ics:.2f}")
    print(f"  completeness_score        : {cs}")
    print(f"  regulatory_coverage_pct   : {rc}")
    print(f"  final_verdict             : {verdict}")
    print(f"  T17 articles              : {len(t17.get('articles', []))}")
    print(f"  T18 rendered_report       : {(t18.get('rendered_report') or {}).get('renderer')}")

    if failures:
        print()
        print(f"FAILED — {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  ✗ {f}")
        return 1

    print()
    print("PASSED — all 12 workflow stages executed, KPI gates met, T17/T18 valid ✓")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_run()))
