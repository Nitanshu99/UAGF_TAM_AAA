"""
Demo script: exercises the full data-persistence cycle.
Run with:  AAA_DATA_DIR=/tmp/aaa_demo_data python scripts/demo_data_store.py
"""
import json
import os
import subprocess

os.environ.setdefault("AAA_DATA_DIR", "/tmp/aaa_demo_data")
os.environ.setdefault("AAA_OFFLINE_MODE", "true")

from aaa.data.models import EngagementRecord, UploadedFileMeta
from aaa.data.writer import save_engagement, save_intake, save_uploaded_file, save_result
from aaa.data.reader import load_engagement, load_intake, load_full_result, list_engagements, list_results

EID = "demo-eng-001"

# 1. User creates an engagement
save_engagement(EngagementRecord(
    engagement_id=EID,
    provider_name="Acme Corp",
    system_name="CreditBot v2",
    declared_risk_tier="high",
    cgsa_assessment_id=None,
    status="created",
))
print("✓ Engagement saved")

# 2. User submits intake
save_intake(
    engagement_id=EID,
    stage_a={"declared_modality": "tabular", "declared_risk_tier": "high",
             "intended_purpose": "credit scoring", "deployment_context": "b2b",
             "provider_name": "Acme Corp"},
    stage_b={"general_description": "XGBoost credit risk model"},
    stage_c=None,
)
print("✓ Intake saved")

# 3. User uploads a file
save_uploaded_file(UploadedFileMeta(
    engagement_id=EID,
    filename="risk_mgmt.pdf",
    role="risk_management_file",
    content_type="application/pdf",
    bytes_size=2048,
    sha256="abc123deadbeef",
    uri="minio://demo-eng-001/risk_mgmt.pdf",
))
print("✓ Uploaded file metadata saved")

# 4. Pipeline writes audit result
save_result(EID, {
    "final_verdict": "PASS_WITH_OBSERVATIONS",
    "intake_completeness_score": 0.88,
    "completeness_score": 0.91,
    "regulatory_coverage_pct": 87.5,
    "material_findings_count": 0,
    "possibly_material_findings_count": 2,
    "auditor_opinion": "System demonstrates reasonable compliance with EU AI Act.",
    "art43_decision": {"procedure": "internal_control", "rationale": "No Annex III sec 1."},
    "blocking_findings": [],
    "positive_findings": [{"id": "pf1", "title": "Data governance documented"}],
    "remediation_roadmap": [{"action": "Add post-market monitoring plan"}],
    "compliance_matrix": {"Art.5": "PASS", "Art.10": "PASS", "Art.13": "PASS"},
    "phase_artefacts": {"T02_system_card": {"uri": "minio://demo-eng-001/T02"}},
})
print("✓ Audit result saved")

# 5. Read back
print("\n=== Index (all engagements) ===")
for row in list_engagements():
    print(json.dumps(row, indent=2))

print("\n=== Completed results ===")
for row in list_results():
    print(f"  {row['engagement_id']} → {row['final_verdict']}")

print("\n=== Engagement record (user input) ===")
print(json.dumps(load_engagement(EID), indent=2))

print("\n=== Intake (stage_a excerpt) ===")
intake = load_intake(EID) or {}
print(json.dumps(intake.get("stage_a"), indent=2))

print("\n=== Full result (audit_result section) ===")
full = load_full_result(EID) or {}
for key in ["final_verdict", "completeness_score", "regulatory_coverage_pct",
            "auditor_opinion", "art43_procedure"]:
    print(f"  {key}: {full.get(key)}")

print("\n=== Folder layout ===")
data_dir = os.environ["AAA_DATA_DIR"]
subprocess.run(["find", data_dir, "-type", "f", "-not", "-name", "*.tmp"], check=True)
