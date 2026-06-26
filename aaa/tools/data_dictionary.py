"""
aaa.tools.data_dictionary — Resolve how to split a client dataset for analysis.

To independently re-run metrics, fairness, and robustness, the phase agents must
know (a) which column is the prediction target, (b) which label counts as the
favourable/positive outcome, and (c) which columns are protected attributes for
fairness testing.

A real auditor expects this in the technical documentation. When the client
supplied it (Stage B ``data_dictionary`` or top-level keys) we use it verbatim;
otherwise we derive it defensively from the column names and **record every
assumption** so the calling agent can raise it as a finding rather than proceeding
silently on a guess.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Column-name patterns that flag a likely protected attribute (EU AI Act Art. 10(2)(f)
# / non-discrimination). Matched case-insensitively as whole-word-ish substrings.
_SENSITIVE_PATTERNS = re.compile(
    r"(?:^|_)(age|sex|gender|marital|personal_status|race|ethnic|nationalit|"
    r"national_origin|foreign|religio|disab|pregnan|sexual_orientation|"
    r"political|migrant|citizenship)",
    re.IGNORECASE,
)


@dataclass
class DataDictionary:
    """Resolved split contract for a tabular dataset."""

    target_column: str | None
    positive_label: Any
    sensitive_feature_columns: list[str]
    feature_columns: list[str]
    assumptions: list[str] = field(default_factory=list)
    target_explicit: bool = False
    sensitive_explicit: bool = False

    def is_usable(self) -> bool:
        """True when we have a target and at least one feature to predict from."""
        return bool(self.target_column) and bool(self.feature_columns)


def _explicit_block(stage_b: dict[str, Any]) -> dict[str, Any]:
    """Pull an explicit data dictionary from Stage B (nested or top-level)."""
    block = dict(stage_b.get("data_dictionary") or {})
    for key in ("target_column", "positive_label", "sensitive_feature_columns", "feature_columns"):
        if key not in block and stage_b.get(key) is not None:
            block[key] = stage_b[key]
    return block


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

    # ── target ────────────────────────────────────────────────────────────────
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

    # ── sensitive columns ──────────────────────────────────────────────────────
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
