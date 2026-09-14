"""The T08 compliance narrative: what the special-category log can and cannot say."""
from __future__ import annotations


def _unresolved(pii_result: dict) -> str:
    """Sentences for mentions the scan found but could not place in an Art. 9 category.

    An NRP match is kept visible with the words it matched — "german", "english" in
    case 05's CVs — so the reader can resolve it; it is not a detected category
    (T-20260913-096).
    """
    return "".join(
        f" The PII scan found {m.get('entity_type')} mentions in column "
        f"'{m.get('column_name')}' ({m.get('sample_count')} sampled cell(s); matched terms: "
        f"{', '.join(m.get('matched_terms') or []) or 'not recorded'}): it "
        f"{m.get('reason')}, so no category is recorded from it."
        for m in pii_result.get("unresolved_mentions") or [])


def narrative(present: bool, categories: list, pii_result: dict) -> str:
    """The T08 narrative, never "Categories: none" beside a presence it cannot identify.

    Case 04 declared special-category data, has no category list in the intake and
    no dataset to scan; T08 said "Categories: none" and "review not applicable"
    (T-20260913-079).
    """
    if not present:
        return ("Special-category data absent. Art. 10 §5 / GDPR Art. 9 review not applicable."
                + _unresolved(pii_result))
    if categories:
        return (f"Special-category data present. Categories: {categories}. "
                "Art. 10 §5 / GDPR Art. 9 review required." + _unresolved(pii_result))
    scanned = pii_result.get("analyser_engine") is not None
    return ("Special-category data present as declared, but its categories are not identified: "
            "the intake declares none"
            + (" and the PII scan detected none." if scanned else " and no dataset was scanned.")
            + " Art. 10 §5 / GDPR Art. 9 review required: the provider must identify each "
              "category and its lawful basis.")
