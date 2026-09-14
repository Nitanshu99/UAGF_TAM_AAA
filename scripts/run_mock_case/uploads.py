"""Uploading the mock case's model, datasets and client documents."""
from __future__ import annotations

import pathlib
import sys
from typing import Any

from scripts.run_mock_case.env import DOC_FIELDS, REPO_ROOT


def content_type(path: pathlib.Path) -> str:
    """Best-effort MIME type for an uploaded document by file extension."""
    return {
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".json": "application/json",
        ".csv": "text/csv",
        ".pdf": "application/pdf",
        ".docx": ("application/vnd.openxmlformats-officedocument"
                  ".wordprocessingml.document"),
    }.get(path.suffix.lower(), "application/octet-stream")


def upload_case_files(client: Any, eid: str, case_dir: pathlib.Path,
                      stage_b: dict[str, Any]) -> None:
    """Upload model / datasets / referenced docs; rewrite Stage B URIs in place.

    :param client: FastAPI test client.
    :param eid: Engagement identifier.
    :param case_dir: The mock case folder.
    :param stage_b: Stage B payload whose URI fields are rewritten to
        ``minio://`` URIs.
    """
    def upload(role: str, path: pathlib.Path, ctype: str) -> str:
        resp = client.post(
            f"/api/v1/engagements/{eid}/files",
            data={"role": role},
            files={"file": (path.name, path.read_bytes(), ctype)})
        return resp.json()["uri"]

    model_dir = case_dir / "model"
    models = sorted(model_dir.glob("*.joblib")) + sorted(model_dir.glob("*.pkl"))
    if models:
        stage_b["model_artifact_uri"] = upload(
            "model_artifact_uri", models[0], "application/octet-stream")
    ds_dir = case_dir / "datasets"
    for name, role in (("evaluation_dataset.csv", "evaluation_dataset_uri"),
                       ("training_dataset.csv", "training_dataset_uri")):
        if (ds_dir / name).exists():
            stage_b[role] = upload(role, ds_dir / name, "text/csv")

    # Upload client documents referenced by Stage B local paths so they land in
    # the EvidenceStore (MinIO); rewrite each field to its minio:// URI so
    # client_doc_ingest can index them during intake.
    for field in DOC_FIELDS:
        ref = stage_b.get(field)
        if not isinstance(ref, str) or not ref or ref.startswith("minio://"):
            continue
        ref_path = pathlib.Path(ref)
        doc_path = ref_path if ref_path.is_absolute() else (REPO_ROOT / ref_path)
        if doc_path.exists():
            stage_b[field] = upload(field, doc_path, content_type(doc_path))
        else:
            print(f"  ⚠ client doc not found, leaving as-is: {ref}", file=sys.stderr)
