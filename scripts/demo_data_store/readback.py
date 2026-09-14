"""Read-back phase of the data-store demo."""
from __future__ import annotations

import json
import os
import subprocess

from scripts.demo_data_store.sample_data import ENGAGEMENT_ID


def read_back() -> None:
    """Read everything back and print the folder layout."""
    from aaa.data.reader import (
        list_engagements,
        list_results,
        load_engagement,
        load_full_result,
        load_intake,
    )

    print("\n=== Index (all engagements) ===")
    for row in list_engagements():
        print(json.dumps(row, indent=2))

    print("\n=== Completed results ===")
    for row in list_results():
        print(f"  {row['engagement_id']} → {row['final_verdict']}")

    print("\n=== Engagement record (user input) ===")
    print(json.dumps(load_engagement(ENGAGEMENT_ID), indent=2))

    print("\n=== Intake (stage_a excerpt) ===")
    intake = load_intake(ENGAGEMENT_ID) or {}
    print(json.dumps(intake.get("stage_a"), indent=2))

    print("\n=== Full result (audit_result section) ===")
    full = load_full_result(ENGAGEMENT_ID) or {}
    for key in ["final_verdict", "completeness_score", "regulatory_coverage_pct",
                "auditor_opinion", "art43_procedure"]:
        print(f"  {key}: {full.get(key)}")

    print("\n=== Folder layout ===")
    data_dir = os.environ["AAA_DATA_DIR"]
    subprocess.run(["find", data_dir, "-type", "f", "-not", "-name", "*.tmp"],
                   check=True)
