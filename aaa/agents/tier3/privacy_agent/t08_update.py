"""T08 artefact update for the Tier-3 privacy audit."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aaa.agents.tier2.data_auditor.t08 import _entry


def update_t08(t08: dict[str, Any], engagement_id: str,
               pii_results: dict[str, Any],
               no_scan_reason: str = "") -> tuple[dict[str, Any], list[str]]:
    """Return T08 extended with the deep-dive PII scan outcomes.

    :param t08: The existing T08 payload (may be empty).
    :param engagement_id: Engagement identifier.
    :param pii_results: Results from the specialist ``pii_scan`` run; empty when
        the scan did not run.
    :param no_scan_reason: Why the deep-dive did not run, if it did not. An
        empty scan result and a scan that found nothing are different findings,
        and only the narrative can tell them apart (P5).
    :returns: ``(new_t08, merged_special_categories)``.
    """
    new_t08 = dict(t08)
    new_t08.update({
        "engagement_id": engagement_id,
        "special_category_data_present": (
            t08.get("special_category_data_present")
            or pii_results.get("special_category_data_detected", False)
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    })
    existing_cats = set(t08.get("special_categories_detected", []))
    new_cats = set(pii_results.get("special_categories_found", []))
    merged_cats = list(existing_cats | new_cats)
    if merged_cats:
        new_t08["special_categories_detected"] = merged_cats

    # Entries when data is present but none declared — flagged for DPO review
    # rather than silently omitted, and naming no basis nobody declared: this wrote
    # art9_2g_public_interest, "Client declared general public interest", and
    # dpia_conducted False, all invented (T-20260913-036).
    if new_t08.get("special_category_data_present") and not new_t08.get("lawful_basis_entries"):
        new_t08["lawful_basis_entries"] = [_entry(cat) for cat in merged_cats]
    if no_scan_reason:
        provenance = (
            "DPIA cross-reference and Art. 10 §5 review performed, but the PII "
            f"deep-dive did not run: {no_scan_reason}. The special categories "
            "recorded here are Phase 2's; this review adds no independent scan "
            "evidence for or against further ones."
        )
    else:
        provenance = ("DPIA cross-reference and Art. 10 §5 review performed; the "
                      "evaluation set was re-scanned with "
                      f"{pii_results.get('analyser_engine', 'the PII scanner')}.")
    new_t08["compliance_narrative"] = (
        (t08.get("compliance_narrative") or "")
        + f"\n[Tier-3 Privacy Audit] {provenance}"
    ).strip()
    return new_t08, merged_cats
