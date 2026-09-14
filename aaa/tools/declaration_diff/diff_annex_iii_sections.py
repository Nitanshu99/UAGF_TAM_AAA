"""Part 3 of the former ``declaration_diff`` module (auto-split)."""
from __future__ import annotations

from aaa.tools.declaration_diff.comparable_fields import (  # noqa: F401
    _COMPARABLE_FIELDS,
    _normalise,
)
from aaa.tools.declaration_diff.core import declaration_diff  # noqa: F401


def diff_annex_iii_sections(
    declared_sections: list[str],
    verified_sections: list[str],
) -> dict[str, str]:
    """
    Lightweight diff for the Annex III section lists.

    Each section gets a verdict:
      "match"          — in both declared and verified
      "mismatch"       — in declared but NOT confirmed (not same as rejected)
      "phase1_added"   — in verified but not declared
      "not_verifiable" — in declared but Phase 1 could not assess

    Note: provenance is the authoritative record (on each AnnexIIIEntry);
    this function returns a compact summary for T02's declaration_verification.

    Parameters
    ----------
    declared_sections : list[str]
        Annex III section numbers declared in Stage A.
    verified_sections : list[str]
        Annex III section numbers confirmed by Phase 1.

    Returns
    -------
    dict[str, str]
        Keyed by ``"annex_iii_§{section}"``.
    """
    result: dict[str, str] = {}
    declared_set = set(declared_sections)
    verified_set = set(verified_sections)

    for section in declared_set | verified_set:
        key = f"annex_iii_§{section}"
        if section in declared_set and section in verified_set:
            result[key] = "match"
        elif section in declared_set and section not in verified_set:
            result[key] = "mismatch"
        else:
            result[key] = "not_verifiable"

    return result
