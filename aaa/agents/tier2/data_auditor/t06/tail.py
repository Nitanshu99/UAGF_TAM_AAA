"""Tail sections of the T06 Datasheet for Datasets."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.data_auditor.t06.cited import NOT_DECLARED, Found, cite, performed
from aaa.agents.tier2.data_auditor.t06.subpopulations import impact_on_subpopulations


def preprocessing_section(found: Found) -> dict[str, Any]:
    """Build the datasheet ``preprocessing_cleaning_labelling`` block.

    The Annex IV contract declares no preprocessing or labelling; a step is
    ``True`` only where a document passage says it was done, and ``None`` —
    unknown — otherwise, never ``False``. A description nothing answers is "not
    declared", as every other undeclared text field is (T-20260913-105).
    """
    return {
        "preprocessing_performed": performed(found, "preprocessing"),
        "preprocessing_description": cite(found, "preprocessing") or NOT_DECLARED,
        "labelling_performed": performed(found, "labelling"),
        "labelling_description": cite(found, "labelling") or NOT_DECLARED,
        "label_validation": NOT_DECLARED,
        "raw_data_available": None,
        "software_used": NOT_DECLARED,
    }


def uses_section(t01a: dict, label_bias: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build the datasheet ``uses`` block; subpopulation impact from the measured labels."""
    return {
        "intended_tasks": t01a.get("intended_purpose",
                                   "High-risk AI system training — see system card."),
        "prior_publications": None,
        "prohibited_tasks": (
            "Must not be used for purposes outside the declared intended purpose "
            "or in violation of EU AI Act Art. 5 prohibitions."
        ),
        "impact_on_subpopulations": impact_on_subpopulations(label_bias),
        "other_known_uses": None,
    }


def distribution_section(t01a: dict) -> dict[str, Any]:
    """Build the datasheet ``distribution`` block."""
    return {
        # Was "Internal — not publicly distributed.", asserted of every dataset.
        "distribution_method": NOT_DECLARED,
        "access_url": None,
        "licence": NOT_DECLARED,
        "ip_restrictions": None,
        "regulatory_restrictions": ("GDPR applies." if t01a.get("gdpr_overlap") else None),
        "export_controls": None,
    }


def maintenance_section(t01a: dict, provider: str, found: Found) -> dict[str, Any]:
    """Build the datasheet ``maintenance`` block."""
    return {
        "maintainer": provider,
        "contact": None,
        "update_plan": NOT_DECLARED,
        "errata_process": None,
        "retention_period": cite(found, "retention") or NOT_DECLARED,
        "version": t01a.get("version"),
    }
