"""Part 2 of the former ``data_dictionary`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.tools.data_dictionary.sensitive_patterns import (  # noqa: F401
    _SENSITIVE_PATTERNS,
    DataDictionary,
    _explicit_block,
)


def _resolve_target(block: dict[str, Any], cols: list[str],
                    assumptions: list[str]) -> tuple[Any, bool]:
    """Resolve the prediction-target column, recording assumptions.

    :param block: Explicit data-dictionary block from Stage B.
    :param cols: Actual dataframe columns.
    :param assumptions: Mutable assumption log (appended in place).
    :returns: ``(target_column, was_declared_explicitly)``.
    """
    target = block.get("target_column")
    target_explicit = bool(target)
    if target and cols and target not in cols:
        assumptions.append(
            f"Declared target_column '{target}' is absent from the dataset columns; "
            "falling back to the last column."
        )
        target = None
        target_explicit = False
    if not target and cols:
        target = cols[-1]
        assumptions.append(
            f"No target_column declared in the technical documentation; assumed the last "
            f"column '{target}' is the prediction target. Confirm with the provider."
        )
    return target, target_explicit


def _resolve_sensitive(block: dict[str, Any], cols: list[str], target: Any,
                       assumptions: list[str]) -> tuple[list[str], bool]:
    """Resolve the protected-attribute columns, recording assumptions.

    :param block: Explicit data-dictionary block from Stage B.
    :param cols: Actual dataframe columns.
    :param target: Resolved target column (excluded from inference).
    :param assumptions: Mutable assumption log (appended in place).
    :returns: ``(sensitive_columns, was_declared_explicitly)``.
    """
    sensitive = list(block.get("sensitive_feature_columns") or [])
    sensitive_explicit = bool(sensitive)
    if not sensitive and cols:
        inferred = [c for c in cols if c != target and _SENSITIVE_PATTERNS.search(c)]
        if inferred:
            sensitive = inferred
            assumptions.append(
                "No sensitive_feature_columns declared; auditor-inferred protected "
                f"attributes from column names: {', '.join(inferred)}. Confirm scope of "
                "non-discrimination testing with the provider."
            )
        else:
            assumptions.append(
                "No sensitive_feature_columns declared and none could be inferred from "
                "column names; fairness testing for protected groups could not be scoped."
            )
    return sensitive, sensitive_explicit
