"""A case-06-shaped dossier, synthetic so CI can run it.

Ranking system, no model artefact, an evaluation set declared with a target and
five protected attributes, and seven declared ranking metrics.
"""
from __future__ import annotations

from typing import Any

SENSITIVE = ["age_band", "sex", "nationality", "region", "first_language"]
DECLARED_METRICS = {"precision_at_3": 0.61, "precision_at_5": 0.58, "precision_at_10": 0.52,
                    "ndcg_at_5": 0.71, "ndcg_at_10": 0.79,
                    "baseline_precision_at_5": 0.3, "baseline_ndcg_at_5": 0.45}
STAGE_B: dict[str, Any] = {
    "model_access_mode": "not_provided", "evaluation_dataset_uri": "minio://e/eval.csv",
    "training_data_description": "Trained by the model vendor. Evaluation set: 600 ranked rows.",
    "accuracy_metrics": DECLARED_METRICS,
    "data_dictionary": {"target_column": "advanced", "positive_label": 1,
                        "sensitive_feature_columns": SENSITIVE},
}
T01A: dict[str, Any] = {"provider_name": "Example GmbH", "system_name": "Matcher",
                        "version": "1.0.0", "intended_purpose": "Rank items for search requests."}


def evaluation_frame(rows: int = 600) -> Any:
    """A 600 x 14 frame with the target and the five protected attributes."""
    import pandas as pd

    data: dict[str, Any] = {"advanced": [i % 2 for i in range(rows)]}
    for name in SENSITIVE:
        data[name] = [f"{name}_{i % 3}" for i in range(rows)]
    for i in range(14 - len(data)):
        data[f"f{i}"] = [float(r) for r in range(rows)]
    return pd.DataFrame(data)
