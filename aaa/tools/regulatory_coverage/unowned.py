"""The articles no artefact in the catalogue evidences, and why each one is unowned."""
from __future__ import annotations

from typing import Final

#: In-scope articles no template evidences, each with the reason and the fix that
#: closes it. Declared rather than exempted: the guard asserts this set exactly,
#: so a hole that is not on this list fails the build.
#: Shared by Annex XI and Annex XII.
_GPAI_ANNEXES: Final = (
    "GPAI technical documentation. In `ARTICLE_SET['gpai']` and in no template map at "
    "all — a GPAI-tier engagement has never been run, and this is the gap that run "
    "would find first.")
KNOWN_UNOWNED: Final[dict[str, str]] = {
    "Art.50": (
        "Transparency toward natural persons. No artefact in the catalogue carries "
        "disclosure evidence. It looked owned until fix 47, which found "
        "_TEMPLATE_ARTICLES attributing it to the two output-fairness artefacts — "
        "they examine outputs for bias and say nothing about disclosure, and case 05 "
        "delivered `Art.50 = PASS` on an output sampling log as a result. Closing "
        "this needs a new artefact, not a re-attribution (finding R9)."),
    # Gate-only: these reach an engagement through a Stage A flag rather than a
    # tier, so no ARTICLE_SET lists them and the tier guard cannot see them. Both
    # are unowned all the same, and case 03 delivered Art. 27 as
    # INSUFFICIENT_EVIDENCE for exactly this reason.
    "Art.25": (
        "Responsibilities along the value chain — an entity that assumes provider "
        "obligations. Raised by `become_provider_under_art25`; no template evidences "
        "it."),
    "Art.27": (
        "Fundamental-rights impact assessment. Raised by `triggers_fria` for a public-body "
        "deployer outside Annex III point 2; no template evidences it."),
    "Annex_XI": _GPAI_ANNEXES, "Annex_XII": _GPAI_ANNEXES,
}


__all__ = ["KNOWN_UNOWNED", "_GPAI_ANNEXES"]
