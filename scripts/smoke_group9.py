#!/usr/bin/env python3
"""
smoke_group9.py — Smoke test for Group 9 (Phase 6 ReportArchitect).

Instantiates ReportArchitect directly (bypassing the full orchestrator) and
validates:
  1. T17 and T18 artefacts are stored in the EvidenceStore.
  2. T17 payload satisfies its JSON-Schema (draft-07) constraints.
  3. T18 payload satisfies its JSON-Schema (draft-07) constraints.
  4. final_verdict is one of PASS / PASS_WITH_OBSERVATIONS / FAIL.
  5. rendered_report block is present with a valid json_uri.
  6. All in-scope articles appear in T17.articles.
  7. Report carries tool_calls for template_render and report_render.

Run from the repository root:
    python scripts/smoke_group9.py

Exit code 0 = all assertions passed.
Exit code 1 = one or more checks failed.
"""
from __future__ import annotations

import asyncio
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.agents.base import Dispatch
from src.agents.tier2.report_architect import ReportArchitect
from src.platform.evidence import EvidenceStore

_ENGAGEMENT = "smoke-group9-001"
_VALID_VERDICTS = {"PASS", "PASS_WITH_OBSERVATIONS", "FAIL"}

# Synthetic compliance matrix covering a "high" risk-tier engagement
_COMPLIANCE_MATRIX = {
    "Art.9": "PASS", "Art.10": "PASS_WITH_OBSERVATIONS",
    "Art.13": "PASS", "Art.14": "PASS",
    "Art.15": "PASS_WITH_OBSERVATIONS", "Art.17": "PASS",
    "Art.43": "PASS", "Annex_III": "PASS", "Annex_IV": "PASS",
}

# Synthetic admitted phase artefacts (non-stub URIs)
_PHASE_ARTEFACTS = {
    tid: {"uri": f"minio://{_ENGAGEMENT}/phase_x/{tid}_abc12345.json",
          "sha256": "abc1234567890", "template_id": tid}
    for tid in [
        "T02_system_card", "T03_annex_iii_mapping", "T04_risk_tier_decision",
        "T05_art43_decision", "T06_datasheet_for_datasets", "T07_data_quality_report",
        "T08_special_category_data_log", "T09_model_card", "T10_explainability_report",
        "T11_robustness_report", "T12_output_fairness_report", "T13_output_sampling_log",
        "T14_governance_findings", "T15_monitoring_logging_review",
    ]
}

# Synthetic verifier critiques
_CRITIQUES = {
    tid: {"verdict": "accept", "issues": [], "notes": ["smoke stub"],
          "article_citations": ["Art.9", "Art.10", "Art.13"],
          "rerun_required": False}
    for tid in _PHASE_ARTEFACTS
}


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
    agent = ReportArchitect(evidence_store=store)

    dispatch = Dispatch(
        phase_id="P6",
        task_brief="Smoke-test run of Phase 6 ReportArchitect.",
        evidence_uris=[ref["uri"] for ref in _PHASE_ARTEFACTS.values()],
        output_contract="T18_audit_report",
        declaration_summary={
            "engagement_id": _ENGAGEMENT,
            "stage_a": {
                "provider_name": "Smoke Corp",
                "system_name": "smoke-ai-v1",
                "version": "1.0",
                "intended_purpose": "Smoke test classification",
            },
            "risk_tier": "high",
            "modality": "tabular",
            "deployment_context": "b2b",
            "is_llm_or_agentic": False,
            "annex_iii_sections": ["1", "2"],
            "art43_decision": {"procedure": "annex_vi_internal_control",
                               "rationale": "Standard high-risk control."},
            "compliance_matrix": _COMPLIANCE_MATRIX,
            "phase_artefacts": _PHASE_ARTEFACTS,
            "verifier_critiques": _CRITIQUES,
            "blocking_findings": [],
            "positive_findings": [],
            "remediation_roadmap": [],
            "intake_completeness_score": 0.95,
            "completeness_score": 0.92,
            "regulatory_coverage_pct": 100.0,
            "final_verdict": "PASS",
            "cgsa_report_url": None,
            "hitl_required": False,
            "hitl_reason": None,
            "verifier_summary": {"accept": len(_CRITIQUES)},
        },
    )

    print("Running ReportArchitect.process() ...")
    report = await agent.process(dispatch)
    print(f"  summary : {report.get('summary')}")
    print(f"  confidence : {report.get('confidence')}")

    failures: list[str] = []

    # ── 1. Report structure ───────────────────────────────────────────────────
    for field in ("phase_id", "artefact_uri", "summary", "confidence",
                  "tool_calls", "declaration_verification_delta"):
        if field not in report:
            failures.append(f"Report missing field '{field}'")

    delta = report.get("declaration_verification_delta", {})
    artefacts = delta.get("phase_artefacts", {})
    for tid in ("T17_compliance_matrix", "T18_audit_report"):
        if tid not in artefacts:
            failures.append(f"delta.phase_artefacts missing '{tid}'")

    # ── 2. EvidenceStore ─────────────────────────────────────────────────────
    index = store.get_index(_ENGAGEMENT)
    stored_types = {e["artefact_type"] for e in index}
    for tid in ("T17_compliance_matrix", "T18_audit_report"):
        if tid not in stored_types:
            failures.append(f"EvidenceStore missing artefact '{tid}'")

    t17_uri = artefacts.get("T17_compliance_matrix", {}).get("uri", "")
    t18_uri = artefacts.get("T18_audit_report", {}).get("uri", "")
    t17 = store.get_artefact(t17_uri) or {}
    t18 = store.get_artefact(t18_uri) or {}

    # ── 3. Schema validation ──────────────────────────────────────────────────
    failures += _validate_schema(t17, _load_schema("T17_compliance_matrix"), "T17")
    failures += _validate_schema(t18, _load_schema("T18_audit_report"), "T18")

    # ── 4. Semantic checks ────────────────────────────────────────────────────
    if t17.get("final_verdict") not in _VALID_VERDICTS:
        failures.append(f"T17.final_verdict invalid: {t17.get('final_verdict')!r}")
    if t18.get("final_verdict") not in _VALID_VERDICTS:
        failures.append(f"T18.final_verdict invalid: {t18.get('final_verdict')!r}")

    t17_articles = {row["article"] for row in (t17.get("articles") or [])}
    for art in _COMPLIANCE_MATRIX:
        if art not in t17_articles:
            failures.append(f"T17.articles missing article '{art}'")

    rendered = t18.get("rendered_report") or {}
    if not rendered.get("json_uri"):
        failures.append("T18.rendered_report.json_uri is empty")
    if rendered.get("renderer") not in {"reportlab", "text_fallback"}:
        failures.append(f"T18.rendered_report.renderer invalid: {rendered.get('renderer')!r}")

    # ── 5. Tool call trace ────────────────────────────────────────────────────
    tool_names = [tc["tool"] for tc in report.get("tool_calls", [])]
    if "template_render" not in tool_names:
        failures.append("tool_calls missing 'template_render'")
    if "report_render" not in tool_names:
        failures.append("tool_calls missing 'report_render'")

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    if failures:
        print(f"FAILED — {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  ✗ {f}")
        return 1
    else:
        print("PASSED — all checks passed ✓")
        print(f"  T17 final_verdict  : {t17.get('final_verdict')}")
        print(f"  T18 final_verdict  : {t18.get('final_verdict')}")
        print(f"  T17 articles       : {len(t17.get('articles', []))}")
        print(f"  Renderer           : {rendered.get('renderer')}")
        print(f"  json_uri           : {rendered.get('json_uri')}")
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_run()))
