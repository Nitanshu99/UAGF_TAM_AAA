"""Write phase of the data-store demo: engagement, intake, file, result."""
from __future__ import annotations

from scripts.demo_data_store.sample_data import AUDIT_RESULT, ENGAGEMENT_ID, STAGE_A, STAGE_B


def seed() -> None:
    """Persist one demo engagement through all four write paths."""
    from aaa.data.models import EngagementRecord, UploadedFileMeta
    from aaa.data.writer import save_engagement, save_intake, save_result, save_uploaded_file

    save_engagement(EngagementRecord(
        engagement_id=ENGAGEMENT_ID,
        provider_name="Acme Corp",
        system_name="CreditBot v2",
        declared_risk_tier="high",
        cgsa_assessment_id=None,
        status="created",
    ))
    print("✓ Engagement saved")

    save_intake(engagement_id=ENGAGEMENT_ID, stage_a=STAGE_A,
                stage_b=STAGE_B, stage_c=None)
    print("✓ Intake saved")

    save_uploaded_file(UploadedFileMeta(
        engagement_id=ENGAGEMENT_ID,
        filename="risk_mgmt.pdf",
        role="risk_management_file",
        content_type="application/pdf",
        bytes_size=2048,
        sha256="abc123deadbeef",
        uri="minio://demo-eng-001/risk_mgmt.pdf",
    ))
    print("✓ Uploaded file metadata saved")

    save_result(ENGAGEMENT_ID, AUDIT_RESULT)
    print("✓ Audit result saved")
