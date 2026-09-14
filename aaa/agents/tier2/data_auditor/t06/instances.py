"""What the datasheet's instances are, without mixing up two datasets or two counts.

``instances_type`` quoted the declared training-data description while every count
in the datasheet was measured on the evaluation set: FinClear's datasheet said
"1000 instances" beside ``num_instances: 700`` and the Verifier held T06 for the
contradiction (case 01, 2026-09-13). When the examined file *is* the declared
training set, the declaration can still state other counts — FinClear declares 1,000
instances and 20 attributes and supplies 700 rows (MiniMax run, 2026-09-14) — so the
measured counts follow the declaration and a differing declared count is named.
"""
from __future__ import annotations

from aaa.agents.tier2.data_auditor.declared_counts import (
    count_differences,
    counts_phrase,
    feature_count,
)
from aaa.agents.tier2.data_auditor.t06.measured import DatasetMeasurement


def instances_type(training_desc: str, measured: DatasetMeasurement | None,
                   role: str | None, target: str | None = None) -> str:
    """The dataset examined, with its measured counts beside what was declared.

    :param training_desc: The declared ``training_data_description``.
    :param measured: The dataset Phase 2 measured, or ``None``.
    :param role: ``"training"`` when that dataset is the declared training set.
    :param target: The declared target column, not counted as an attribute.
    """
    if measured is None:
        return training_desc
    features = feature_count(measured, target)
    counts = counts_phrase(measured, target)
    if role == "training":
        return (f"{training_desc} Measured on the supplied training set ({measured.dataset_uri}): "
                f"{counts}.{count_differences(training_desc, measured.num_rows, features)}")
    return (f"Dataset examined: {measured.dataset_uri} ({counts}). Declared training data, a "
            f"different dataset whose counts are not measured here: {training_desc}")


__all__ = ["feature_count", "instances_type"]
