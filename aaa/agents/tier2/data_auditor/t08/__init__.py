"""T08 Special Category Data Log assembly.

A detected category is recorded with what is known about it and nothing more.
The builder used to write, for every detected category, a lawful basis of Art. 10
§5 bias correction, a statement that the data is retained for that purpose, and
that DPA consultation is required — none declared by the provider and none
established by the audit (T-20260913-036). No intake contract field carries a
lawful basis, so it is recorded as ``not_declared`` and left to DPO review.
"""
from __future__ import annotations

from aaa.agents.tier2.data_auditor.t08.art10_5 import art10_5_assessment
from aaa.agents.tier2.data_auditor.t08.narrative import narrative
from aaa.tools.document_evidence import Evidence

#: What an entry says when the provider declared no basis for a detected category.
NOT_DECLARED_REFERENCE = ("No lawful basis for this category is declared in the intake; "
                          "detected by the PII scan and pending DPO review.")


def _entry(category: str) -> dict:
    """One lawful-basis entry for a detected category, asserting nothing undeclared."""
    return {
        "special_category": category,
        "lawful_basis": "not_declared",
        "basis_reference": NOT_DECLARED_REFERENCE,
        "dpa_consultation_required": None,
        "dpia_conducted": None,
        "dpia_reference": None,
        "data_minimisation_confirmed": None,
        "retention_period": None,
    }


def build_t08(engagement_id: str, special_cat_present: bool, pii_result: dict,
              undeclared_special_cat: bool, now: str,
              found: dict[str, Evidence | None] | None = None) -> dict:
    """Build the T08 Special Category Data Log.

    :param engagement_id: Engagement identifier.
    :param special_cat_present: Declared or detected special-category flag.
    :param pii_result: ``pii_scan`` output (detected categories).
    :param undeclared_special_cat: True when detection contradicts the declaration.
    :param now: ISO-8601 generation timestamp.
    :param found: Grounded document answers; ``art10_5`` holds a declared Art. 10(5) reliance.
    :returns: The T08 payload matching the template schema.
    """
    categories = pii_result.get("special_categories_found", [])
    entries = [_entry(cat) for cat in categories]
    applies, rationale = art10_5_assessment((found or {}).get("art10_5"), special_cat_present)
    return {
        "engagement_id": engagement_id,
        "special_category_data_present": special_cat_present,
        "special_categories_detected": categories,
        "lawful_basis_entries": entries,
        # Whether data is processed under Art. 10 §5 is the provider's to declare; a
        # declaration is quoted and set against what was declared or detected.
        "art10_5_statistical_correction_applies": applies,
        "statistical_correction_rationale": rationale,
        "privacy_tier3_triggered": special_cat_present,
        "hitl_review_required": undeclared_special_cat,
        "hitl_review_reason": (
            "Undeclared special-category data detected by PII scan. "
            "Human review required before processing continues."
            if undeclared_special_cat else None
        ),
        "compliance_narrative": narrative(special_cat_present, categories, pii_result)
                                + (f" {rationale}" if applies is False else ""),
        "generated_at": now,
    }
