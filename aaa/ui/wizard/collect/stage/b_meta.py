"""Model-meta and data-dictionary collection helpers for the Stage B payload.

Resolves the six S6 hand-off fields from wizard session state, handling both
widget generations (column-aware selectbox/multiselect vs free-text inputs).
"""
from __future__ import annotations

# Any: streamlit's SessionStateProxy is Mapping[Key, Any] (Key != str), so a
# precise Mapping[str, Any] annotation is rejected by pyright at call sites.
from typing import Any

from aaa.ui.wizard.collect.model_reference import model_reference_fields
from aaa.ui.wizard.step3.ranking_columns import RANKING_FIELDS


def _target(s: Any) -> str:
    """Resolve the target column from the selectbox or free-text key.

    :param s: Wizard session state (mapping-like).
    :type s: Any
    :returns: The target column name, possibly empty.
    :rtype: str
    """
    return str(s.get("s3_b_dd_target_sel") or s.get("s3_b_dd_target") or "").strip()


def _sensitive(s: Any) -> list[str]:
    """Resolve sensitive feature columns from the multiselect or comma text.

    :param s: Wizard session state (mapping-like).
    :type s: Any
    :returns: Sensitive feature column names, possibly empty.
    :rtype: list[str]
    """
    selected = s.get("s3_b_dd_sensitive_ms")
    if selected:
        return [str(x) for x in selected]
    return [x.strip() for x in str(s.get("s3_b_dd_sensitive") or "").split(",") if x.strip()]


def _columns(s: Any, key: str) -> list[str] | None:
    """Read one column multiselect, normalising an empty selection to ``None``.

    :param s: Wizard session state (mapping-like).
    :param key: Session-state key of the multiselect.
    :returns: Selected column names, or ``None`` when nothing was selected.
    """
    return [str(x) for x in (s.get(key) or [])] or None


def _ranking(s: Any) -> dict[str, str] | None:
    """Resolve the declared ranking columns — only a complete pair of distinct columns.

    :param s: Wizard session state (mapping-like).
    :returns: ``{query_column, rank_column}``, or ``None`` when either is unset or they coincide.
    """
    pair = {field: str(s.get(select_key) or s.get(text_key) or "").strip()
            for field, (_, select_key, text_key, _) in RANKING_FIELDS.items()}
    values = list(pair.values())
    return pair if all(values) and len(set(values)) == len(values) else None


def model_meta_fields(s: Any) -> dict[str, Any]:
    """Assemble the S6 hand-off fields for the stage_b top level.

    :param s: Wizard session state (mapping-like).
    :type s: Any
    :returns: ``target_column``, ``positive_label``, ``sensitive_feature_columns``,
        ``immutable_feature_columns``, ``actionable_feature_columns``,
        ``task_type``, ``model_format``, ``model_framework``,
        ``model_artifact_kind``, ``model_entrypoint`` — unset values ``None``.
    :rtype: dict[str, Any]
    """
    fields: dict[str, Any] = {
        "target_column": _target(s) or None,
        "positive_label": str(s.get("s3_b_dd_positive") or "").strip() or None,
        "sensitive_feature_columns": _sensitive(s) or None,
        "immutable_feature_columns": _columns(s, "s3_b_dd_immutable_ms"),
        "actionable_feature_columns": _columns(s, "s3_b_dd_actionable_ms"),
    }
    for key in ("task_type", "model_format", "model_framework",
                "model_artifact_kind", "model_entrypoint"):
        fields[key] = str(s.get(f"s3_b_{key}") or "").strip() or None
    fields.update(model_reference_fields(s))
    return fields


def data_dictionary_block(s: Any) -> dict[str, Any]:
    """Build the legacy data-dictionary block (kept for backward compatibility).

    :param s: Wizard session state (mapping-like).
    :type s: Any
    :returns: Non-empty data-dictionary entries only; ``ranking`` when both columns are declared.
    :rtype: dict[str, Any]
    """
    fields = model_meta_fields(s)
    keys = ("target_column", "positive_label", "sensitive_feature_columns")
    block = {k: fields[k] for k in keys if fields[k]}
    ranking = _ranking(s)
    if ranking:
        block["ranking"] = ranking
    return block
