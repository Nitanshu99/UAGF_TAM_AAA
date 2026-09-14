"""Part 3 of the former ``data_dictionary`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.tools.data_dictionary.resolve.target import (  # noqa: F401
    _resolve_sensitive,
    _resolve_target,
)
from aaa.tools.data_dictionary.sensitive_patterns import (  # noqa: F401
    _SENSITIVE_PATTERNS,
    DataDictionary,
    _explicit_block,
)


def resolve_data_dictionary(
    stage_b: dict[str, Any] | None,
    columns: list[str] | None = None,
) -> DataDictionary:
    """Resolve the target / positive label / sensitive columns for a dataset.

    Parameters
    ----------
    stage_b:
        The Annex IV dossier (may carry an explicit ``data_dictionary``).
    columns:
        Actual dataframe columns. Required for defensive derivation when the
        client did not declare a data dictionary.
    """
    stage_b = stage_b or {}
    cols = list(columns or [])
    block = _explicit_block(stage_b)
    assumptions: list[str] = []

    target, target_explicit = _resolve_target(block, cols, assumptions)

    # ── positive label ──────────────────────────────────────────────────────────
    positive_label = block.get("positive_label", 1)
    if "positive_label" not in block:
        assumptions.append(
            f"No positive_label declared; assumed '{positive_label}' is the favourable "
            "outcome for fairness analysis."
        )

    # ── feature columns ───────────────────────────────────────────────────────
    feature_columns = list(block.get("feature_columns") or [])
    if not feature_columns and cols:
        feature_columns = [c for c in cols if c != target]

    sensitive, sensitive_explicit = _resolve_sensitive(block, cols, target, assumptions)

    return DataDictionary(
        target_column=target,
        positive_label=positive_label,
        sensitive_feature_columns=sensitive,
        feature_columns=feature_columns,
        assumptions=assumptions,
        target_explicit=target_explicit,
        sensitive_explicit=sensitive_explicit,
    )


__all__ = ["DataDictionary", "resolve_data_dictionary"]
