"""Smoke test for Group 6 - Phase 3 Model Validator."""
import asyncio
import json
import sys
import pathlib
from jsonschema import Draft7Validator

from src.platform.evidence import EvidenceStore
from src.agents.tier1.orchestrator import Orchestrator

stage_a = {
    "provider_name": "Acme Credit AI Ltd.",
    "deployer_name": "Sample Bank",
    "system_name": "CreditScoreV2",
    "version": "2.1.0",
    "intended_purpose": "Assess creditworthiness of loan applicants based on tabular features.",
    "declared_modality": "tabular",
    "declared_risk_tier": "high",
    "declared_annex_iii_sections": ["5"],
    "deployment_context": "b2b",
    "provider_elects_third_party": False,
    "gdpr_overlap": True,
    "gpai_general_purpose": False,
    "special_category_data": False,
    "art43_preview": "annex_vi_internal_control",
    "cgsa_assessment_id": None,
}
stage_b = {
    "general_description": "Tabular gradient-boosted classifier for credit scoring trained on UCI German Credit.",
    "model_type": "gradient_boosted_trees",
    "design_process": "XGBoost classifier with hyperparameter tuning; cross-validated on 80/20 split.",
    "training_data_description": "UCI German Credit Data - 1000 instances, 20 attributes, binary creditworthy label.",
    "data_governance_measures": "Data minimisation applied; access restricted; provenance documented per Art. 10 (2).",
    "monitoring_measures": "Monthly performance review and drift detection plan in place.",
    "logging_capabilities": "Predictions logged with timestamp and feature vector hash per Art. 12.",
    "accuracy_metrics": {"accuracy": 0.78, "auc": 0.82},
    "robustness_metrics": None,
    "risk_management_file_uri": None,
    "lifecycle_change_log": ["v2.0 initial release", "v2.1 retrained on Q3 data"],
    "harmonised_standards": [],
    "other_standards": [],
    "eu_doc_uri": None,
    "post_market_plan_uri": None,
    "system_prompt_uri": None,
    "rag_manifest_uri": None,
    "tool_inventory": None,
    "guardrail_config_uri": None,
    "golden_set_uri": None,
}
client_submission = {
    "engagement_id": "eng-smoke-006",
    "stage_a": stage_a,
    "stage_b": stage_b,
    "stage_c": None,
    # Pre-pass Stage 0 gate (>= 0.80) — Group 6 smoke focuses on Phase 3.
    "intake_completeness_score": 0.95,
}

store = EvidenceStore()
orch = Orchestrator(evidence_store=store)
final = asyncio.run(orch.process({
    "engagement_id": client_submission["engagement_id"],
    "client_submission": client_submission,
}))
print("intake_completeness_score=", final.get("intake_completeness_score"))

arts = final.get("phase_artefacts", {})
print("Phase 3 artefacts present:")
for tid in ["T09_model_card", "T10_explainability_report", "T11_robustness_report"]:
    a = arts.get(tid, {})
    print(" ", tid, "->", a.get("uri"))

# Validate the stored payloads against their schemas
tpl_dir = pathlib.Path("src/templates")
all_ok = True
for tid in ["T09_model_card", "T10_explainability_report", "T11_robustness_report"]:
    a = arts.get(tid, {})
    uri = a.get("uri", "")
    if not uri:
        print("  SKIP", tid, "(no URI)")
        all_ok = False
        continue
    payload = store.get_artefact(uri) if hasattr(store, "get_artefact") else None
    if payload is None:
        # Try alternate accessor patterns used by EvidenceStore
        for attr in ("read", "load", "get"):
            fn = getattr(store, attr, None)
            if callable(fn):
                try:
                    payload = fn(uri)
                    if payload is not None:
                        break
                except Exception:
                    pass
    if payload is None:
        print("  MISSING payload for", tid, "at", uri)
        all_ok = False
        continue
    schema = json.loads((tpl_dir / f"{tid}.json").read_text())
    errors = sorted(Draft7Validator(schema).iter_errors(payload), key=lambda e: list(e.path))
    if errors:
        all_ok = False
        for err in errors:
            print("  SCHEMA ERROR", tid, list(err.path), err.message[:160])
    else:
        print("  OK", tid, "validates against schema")

# Check verifier critiques
crits = final.get("verifier_critiques", {})
for tid in ["T09_model_card", "T10_explainability_report", "T11_robustness_report"]:
    c = crits.get(tid, {})
    print("  critique", tid, "verdict=", c.get("verdict"), "articles=", c.get("article_citations"))

print("final_verdict=", final.get("final_verdict"))
print("completeness_score=", final.get("completeness_score"))
print("regulatory_coverage_pct=", final.get("regulatory_coverage_pct"))
print("hitl_required=", final.get("hitl_required"))

if all_ok:
    print("SMOKE-TEST PASS")
    sys.exit(0)
else:
    print("SMOKE-TEST FAIL")
    sys.exit(1)
