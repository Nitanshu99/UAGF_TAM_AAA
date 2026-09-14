"""Declared-vs-observed dataset diffing for Phase 2."""
from __future__ import annotations

import re
from typing import Any

from aaa.tools.findings import make_finding


def diff_declared_data(dossier: dict, profile_result: dict) -> list[dict[str, Any]]:
    """Light-touch diff of the declared dataset description vs the real data.

    Conservative on purpose: only the feature-count check, which is stable
    across train/eval splits, to avoid false positives from row-count
    differences between the training and evaluation partitions.

    :param dossier: Annex IV dossier carrying ``training_data_description``.
    :param profile_result: Output of :func:`aaa.tools.data_profile.data_profile`.
    :returns: Findings for material description drift (may be empty).
    """
    desc = str(dossier.get("training_data_description") or "")
    findings: list[dict[str, Any]] = []
    num_cols = profile_result.get("num_columns")
    m = re.search(r"(\d+)\s*attribute", desc, re.IGNORECASE)
    if m and isinstance(num_cols, int) and num_cols > 0:
        declared_attrs = int(m.group(1))
        # The dataset includes the target column; features = columns - 1.
        actual_features = max(num_cols - 1, 0)
        if abs(declared_attrs - actual_features) > 1:
            findings.append(make_finding(
                finding_id="P2-DATA-DIFF-ATTRS",
                description=(
                    f"Declared {declared_attrs} attributes but the supplied dataset has "
                    f"{actual_features} feature columns."
                ),
                materiality="possibly_material",
                articles=["Art.10", "Art.11"],
                source_phase="P2",
                recommendation="Reconcile the Annex IV dataset description with the supplied data.",
                declared=declared_attrs,
                observed=actual_features,
            ))
    return findings
