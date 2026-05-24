#!/usr/bin/env python3
"""
smoke_group8.py — Smoke test for Group 8 (Phase 5 GovernanceAgent).

Instantiates GovernanceAgent directly (bypassing the full orchestrator) and
validates:
  1. cgsa_pull loads the fixture payload (offline mode).
  2. cgsa_ingest validates against the vendored §5.4 schema and hydrates
     every key on the state_delta.
  3. T14 + T15 artefacts are stored in the EvidenceStore.
  4. T14 + T15 payloads satisfy their JSON-Schema (draft-07) constraints.
  5. Risk-tier match, CSP-failure verdict, Tier-3 spawn flags and HITL
     triggers are surfaced correctly on the Report.

Run from the repository root:
    AAA_OFFLINE_MODE=true python scripts/smoke_group8.py

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
os.environ.setdefault(
    "CGSA_FIXTURE_DIR", str(REPO_ROOT / "scripts" / "fixtures" / "cgsa")
)

from src.agents.base import Dispatch  # noqa: E402
from src.agents.tier2.governance_agent import GovernanceAgent  # noqa: E402
from src.platform.evidence import EvidenceStore  # noqa: E402
from src.tools.cgsa_pull import cgsa_pull  # noqa: E402

_ENGAGEMENT = "smoke-group8-eng"
_ASSESSMENT = "smoke-group8-001"


def _load_schema(name: str) -> dict:
    path = REPO_ROOT / "src" / "templates" / f"{name}.json"
    with path.open() as fh:
        return json.load(fh)


def _validate_schema(instance: dict, schema: dict, label: str) -> list[str]:
    errors: list[str] = []
    try:
        import jsonschema  # type: ignore
        try:
            jsonschema.validate(instance, schema)
        except jsonschema.ValidationError as exc:
            errors.append(f"{label}: schema violation — {exc.message}")
    except ImportError:
        print(f"  [WARN] jsonschema not installed — skipping schema validation for {label}.")
    return errors


async def _run() -> int:
    store = EvidenceStore()
    agent = GovernanceAgent(evidence_store=store)

    # ── 1. cgsa_pull (offline fixture) ─────────────────────────────────────
    payload = cgsa_pull(assessment_id=_ASSESSMENT)
    assert payload.get("metadata", {}).get("assessment_id") == _ASSESSMENT

    dispatch = Dispatch(
        phase_id="P5",
        task_brief="Smoke-test run of Phase 5 GovernanceAgent.",
        evidence_uris=[],
        output_contract="T14_governance_findings",
        declaration_summary={
            "engagement_id": _ENGAGEMENT,
            "risk_tier": "high",
            "cgsa_assessment_id": _ASSESSMENT,
            "cgsa_payload": payload,
            "gdpr_overlap": False,
            "special_category_data": True,   # → privacy spawn
            "annex_iii_sections": ["5"],
            "phase3_robustness_verdict": "PASS",
        },
    )

    print("Running GovernanceAgent.process() ...")
    report = await agent.process(dispatch)
    print(f"  summary    : {report.get('summary')}")
    print(f"  confidence : {report.get('confidence')}")

    failures: list[str] = []

    # ── 2. Report structure ───────────────────────────────────────────────
    for field in ("phase_id", "artefact_uri", "summary", "confidence",
                  "tool_calls", "declaration_verification_delta"):
        if field not in report:
            failures.append(f"Report missing field '{field}'")

    delta = report.get("declaration_verification_delta", {})
    artefacts = delta.get("phase_artefacts", {})
    for tid in ("T14_governance_findings", "T15_monitoring_logging_review"):
        if tid not in artefacts:
            failures.append(f"delta.phase_artefacts missing '{tid}'")

    # ── 3. Artefacts in EvidenceStore ─────────────────────────────────────
    stored = {e["artefact_type"] for e in store.get_index(_ENGAGEMENT)}
    for tid in ("T14_governance_findings", "T15_monitoring_logging_review"):
        if tid not in stored:
            failures.append(f"EvidenceStore missing artefact '{tid}'")

    t14 = store.get_artefact(artefacts.get("T14_governance_findings", {}).get("uri", "")) or {}
    t15 = store.get_artefact(artefacts.get("T15_monitoring_logging_review", {}).get("uri", "")) or {}

    # ── 4. Schema validation ──────────────────────────────────────────────
    failures += _validate_schema(t14, _load_schema("T14_governance_findings"), "T14")
    failures += _validate_schema(t15, _load_schema("T15_monitoring_logging_review"), "T15")

    # ── 5. §5.4 hydration on the delta ────────────────────────────────────
    expected_keys = {
        "cgsa_payload", "cgsa_schema_version", "cgsa_composite_maturity_score",
        "cgsa_composite_maturity_label", "cgsa_eu_ai_act_coverage_pct",
        "cgsa_csp_satisfiable", "cgsa_governance_verdict", "cgsa_phase5_verdict",
        "cgsa_phase5_narrative", "cgsa_blocking_findings", "cgsa_positive_findings",
        "cgsa_low_confidence_controls", "cgsa_recommended_follow_up",
        "cgsa_report_url", "cgsa_risk_tier_match", "remediation_roadmap",
        "harmonised_standards_applied",
    }
    for k in expected_keys:
        if k not in delta:
            failures.append(f"delta missing §5.4 hydration key '{k}'")

    # ── 6. CSP failure → FAIL ─────────────────────────────────────────────
    if delta.get("cgsa_csp_satisfiable") is not False:
        failures.append("cgsa_csp_satisfiable expected False from fixture")
    if delta.get("cgsa_phase5_verdict") != "FAIL":
        failures.append(f"cgsa_phase5_verdict expected FAIL, got {delta.get('cgsa_phase5_verdict')!r}")
    if t14.get("phase5_verdict") != "FAIL":
        failures.append("T14.phase5_verdict expected FAIL")

    # ── 7. Risk-tier match ────────────────────────────────────────────────
    if delta.get("cgsa_risk_tier_match") is not True:
        failures.append("cgsa_risk_tier_match expected True (high == high)")
    if t14.get("risk_tier_match", {}).get("match") is not True:
        failures.append("T14.risk_tier_match.match expected True")

    # ── 8. Tier-3 spawn decisions ─────────────────────────────────────────
    if not delta.get("spawn_privacy_subagent"):
        failures.append("spawn_privacy_subagent expected True (special_category_data)")
    if not delta.get("spawn_cyber_subagent"):
        failures.append("spawn_cyber_subagent expected True (risk_tier=high)")

    # ── 9. HITL triggered (CSP fail + low-conf control + blocking follow-up)
    if not delta.get("hitl_required"):
        failures.append("hitl_required expected True (CSP fail + low-confidence + blocking follow-up)")

    # ── 10. Low-confidence controls surfaced ──────────────────────────────
    if not delta.get("cgsa_low_confidence_controls"):
        failures.append("cgsa_low_confidence_controls expected non-empty")
    if not t14.get("low_confidence_controls"):
        failures.append("T14.low_confidence_controls expected non-empty")

    # ── 11. T15 ops verdict + xrefs ───────────────────────────────────────
    if t15.get("overall_ops_verdict") not in {"PASS", "PASS_WITH_OBSERVATIONS", "FAIL", "NOT_APPLICABLE"}:
        failures.append(f"T15.overall_ops_verdict invalid: {t15.get('overall_ops_verdict')!r}")
    if not any(x.get("control_id") == "C30" for x in t15.get("cgsa_cross_references", [])):
        failures.append("T15.cgsa_cross_references expected to lift D6 control C30")

    # ── Summary ───────────────────────────────────────────────────────────
    print()
    if failures:
        print(f"FAILED — {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  ✗ {f}")
        return 1
    print("PASSED — all checks passed ✓")
    print(f"  T14 phase5_verdict       : {t14.get('phase5_verdict')}")
    print(f"  T14 risk_tier_match.match: {t14.get('risk_tier_match', {}).get('match')}")
    print(f"  T15 overall_ops_verdict  : {t15.get('overall_ops_verdict')}")
    print(f"  cyber_spawn / privacy    : {delta.get('spawn_cyber_subagent', False)} / {delta.get('spawn_privacy_subagent', False)}")
    print(f"  hitl_required            : {delta.get('hitl_required', False)}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_run()))
