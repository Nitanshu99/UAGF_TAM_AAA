"""Part 1 of the former ``data_dictionary`` module (auto-split)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

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


def explicit_data_dictionary(stage_b: dict[str, Any]) -> dict[str, Any]:
    """Pull an explicit data dictionary from Stage B (nested or top-level).

    Two shapes are in circulation and both are legitimate. A CLI intake bundle
    nests the block — ``stage_b["data_dictionary"]["target_column"]`` — while the
    wizard also writes the same keys at the top level. Anything that reads only
    the top level therefore works from the UI and silently sees nothing from a
    bundle: the 2026-09-10 baseline dispatched Phase 2 with ``target_column:
    None`` and shipped an S6 hand-off declaring no sensitive features, for an
    engagement whose dossier named five. Use this rather than ``stage_b.get``.

    :param stage_b: The Annex IV dossier.
    :returns: The merged block, nested values taking precedence.
    """
    block = dict(stage_b.get("data_dictionary") or {})
    for key in ("target_column", "positive_label", "sensitive_feature_columns", "feature_columns"):
        if block.get(key) in (None, "", []) and stage_b.get(key) is not None:
            block[key] = stage_b[key]
    return block


#: Kept for the existing internal call sites.
_explicit_block = explicit_data_dictionary
