"""Front sections of the T06 Datasheet for Datasets.

Every value is measured, declared under a contract key, or recorded as unknown.
These builders once read eleven dossier keys no contract defines and hardcoded
``has_labels``, ``sensitive_features`` and ``missing_data_present``, so a datasheet
could assert what nobody measured or declared (T-20260913-009).
``tests/unit/test_dossier_keys_match_contract.py`` keeps the reads honest.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.data_auditor.t06.cited import NOT_DECLARED, Found, cite, timeframe
from aaa.agents.tier2.data_auditor.t06.instances import feature_count
from aaa.agents.tier2.data_auditor.t06.measured import DatasetMeasurement


def motivation_section(t01a: dict, provider: str) -> dict[str, Any]:
    """Build the datasheet ``motivation`` block."""
    return {
        "purpose": t01a.get("intended_purpose")
        or "AI system dataset — purpose inherited from the system card.",
        "creators": provider,
        "funding_sources": NOT_DECLARED,
        "gap_filled": None,
    }


def label_description(dictionary: dict[str, Any]) -> str | None:
    """The declared label, composed from the data dictionary."""
    target = dictionary.get("target_column")
    if not target:
        return None
    positive = dictionary.get("positive_label")
    suffix = f"; positive label `{positive}`" if positive is not None else ""
    return f"Target column `{target}`{suffix}."


def composition_section(t01a: dict, training_desc: str, dictionary: dict[str, Any],
                        measured: DatasetMeasurement | None, found: Found) -> dict[str, Any]:
    """Build the datasheet ``composition`` block from measurement and declaration."""
    target = dictionary.get("target_column")
    missing = measured.missing_columns if measured else ()
    return {
        "instances_type": training_desc,
        "num_instances": measured.num_rows if measured else None,
        "num_features": feature_count(measured, target) if measured else None,
        "has_labels": bool(target) and (measured is None or target in measured.columns),
        "label_description": label_description(dictionary),
        "sensitive_features": [str(c) for c in dictionary.get("sensitive_feature_columns") or []],
        "missing_data_present": bool(missing) if measured else None,
        "missing_data_description": (
            f"{measured.overall_missing_pct}% of cells missing overall; columns with gaps: "
            f"{', '.join(missing)}." if measured and missing else None),
        "confidential_data": bool(t01a.get("special_category_data", False)),
        "relationships_to_other_datasets": cite(found, "relationships") or NOT_DECLARED,
    }


def collection_section(found: Found) -> dict[str, Any]:
    """Build the datasheet ``collection_process`` block from the provider's documents.

    Quoted where a passage answers, otherwise "not declared" — one wording for one fact,
    where a null beside it read to the Verifier as a field left out (T-20260913-105).
    ``consent_obtained`` stays
    ``None`` even where a consent mechanism is described: a description of the
    mechanism is not evidence that consent was obtained for these records.
    """
    return {
        "acquisition_method": cite(found, "acquisition") or NOT_DECLARED,
        "collection_timeframe": timeframe(found),
        "consent_obtained": None,
        "consent_mechanism": cite(found, "consent") or NOT_DECLARED,
        "notification_given": None,
        "third_party_sources": cite(found, "third_party") or NOT_DECLARED,
        "collection_ethical_review": None,
    }
