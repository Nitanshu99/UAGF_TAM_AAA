"""Counts a dataset declaration states, set against the file supplied.

FinClear declares "1000 instances, 20 attributes" and supplies 700 rows (MiniMax runs,
2026-09-14). The datasheet (T06) and the quality report (T07) both describe that file,
and both must name the difference rather than print 700 beside the declared 1000.
"""
from __future__ import annotations

import re

from aaa.agents.tier2.data_auditor.dataset import dataset_role
from aaa.agents.tier2.data_auditor.t06.measured import DatasetMeasurement
from aaa.tools.data_dictionary import explicit_data_dictionary

_ROWS = re.compile(r"(\d[\d,.]*)\s*(?:instances|rows|records|samples|examples)\b", re.I)
_ATTRIBUTES = re.compile(r"(\d[\d,.]*)\s*(?:attributes|features|variables)\b", re.I)


def feature_count(measured: DatasetMeasurement, target: str | None) -> int:
    """Columns other than the declared target."""
    return measured.num_columns - (1 if target and target in measured.columns else 0)


def counts_phrase(measured: DatasetMeasurement, target: str | None) -> str:
    """"600 rows x 14 columns (13 attributes plus the target)" — one wording for every field.

    T06 said "13 attributes plus the target" in one field and "14 columns" in another,
    and the Verifier escalated the pair as a mismatch (case 06, 2026-09-14).
    """
    features = feature_count(measured, target)
    detail = (f" ({features} attributes plus the target)" if features != measured.num_columns
              else "")
    return f"{measured.num_rows} rows x {measured.num_columns} columns{detail}"


def _declared(pattern: re.Pattern[str], text: str) -> int | None:
    """The first count *pattern* finds in *text*, or ``None``."""
    match = pattern.search(text)
    return int(re.sub(r"[,.]", "", match.group(1))) if match else None


def count_differences(training_desc: str, rows: int, features: int) -> str:
    """A sentence naming each declared count the supplied file does not have."""
    gaps = [f"{declared} {name} declared, {measured} supplied"
            for name, declared, measured in (("instances", _declared(_ROWS, training_desc), rows),
                                             ("attributes", _declared(_ATTRIBUTES, training_desc),
                                              features))
            if declared is not None and declared != measured]
    return (f" The declaration and the supplied file differ ({'; '.join(gaps)}); the documents "
            "do not say why (a split, a sample or a later version)." if gaps else "")


def declared_size(t01b: dict, decl: dict, ctx: dict) -> str:
    """The difference sentence for T07, when the file examined is the declared training set.

    :param t01b: Annex IV dossier (declared training description).
    :param decl: Declaration summary (which dataset was examined; the data dictionary).
    :param ctx: Phase 2 analysis context holding the measurement.
    """
    measured = ctx.get("measurement")
    if measured is None or dataset_role(t01b, decl) != "training":
        return ""
    target = explicit_data_dictionary(decl.get("stage_b") or t01b or {}).get("target_column")
    return count_differences(str(t01b.get("training_data_description") or ""),
                             measured.num_rows, feature_count(measured, target))


__all__ = ["count_differences", "counts_phrase", "declared_size", "feature_count"]
