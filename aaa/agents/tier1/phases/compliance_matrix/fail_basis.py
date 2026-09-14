"""Which findings a rationale leads with, and whose analysis a FAIL rests on.

Case 03 (2026-09-13): Art. 15 failed on the provider's own governance finding
C15 ("No adversarial robustness testing", material), yet its rationale opened
with two P3 observations, lost C15 to the length clip, left it out of the
finding ids (a governance finding has a control id, not a finding id) and called
the basis "independent analysis". A reader could not see why the article failed.
"""
from __future__ import annotations

#: Rationale order: the findings that decide a verdict before those that qualify it.
_RANK = {"material": 0, "possibly_material": 1, "observation": 2}


def ordered(findings: list[dict]) -> list[dict]:
    """*findings* most material first, keeping their order within a level.

    :param findings: Findings mapped to one article.
    :returns: The same findings, reordered.
    """
    return sorted(findings, key=lambda f: _RANK.get(str(f.get("materiality")), len(_RANK)))


def finding_ref(finding: dict) -> str:
    """The id a finding is cited by: its finding id, or a governance finding's control id."""
    return str(finding.get("finding_id") or finding.get("control_id") or "")


def fail_basis(findings: list[dict]) -> str:
    """Name whose analysis the material findings behind a FAIL come from.

    :param findings: Findings mapped to the failing article.
    :returns: The opening clause of the FAIL rationale.
    """
    material = [f for f in findings if f.get("materiality") == "material"]
    declared = sum(1 for f in material if f.get("control_id"))
    if material and declared == len(material):
        return "Material non-conformity declared in the provider's governance self-assessment"
    if declared:
        return ("Material non-conformity from independent analysis and the provider's "
                "governance self-assessment")
    return "Material non-conformity from independent analysis"
