"""The two bundles: their names, where they unpack, and the entries that prove them right."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scripts.bootstrap.paths import CASE_DIR, DATA_DIR


class BundleError(RuntimeError):
    """Raised when an archive does not hold what its name promises."""


@dataclass(frozen=True)
class Bundle:
    """One archive, where it unpacks, and the entries that prove it is the right one."""

    name: str
    target: Path
    markers: tuple[str, ...]


BUNDLES: tuple[Bundle, ...] = (
    Bundle("mariposa.zip", CASE_DIR, ("stage_a.json", "stage_b.json", "cgsa", "docs")),
    Bundle("corpus.zip", DATA_DIR, ("eu_ai_act_compliance_checker.json",
                                    "regulatory_corpus/EU_AI_Act.html",
                                    "regulatory_corpus/isae_3000.pdf",
                                    "regulatory_corpus/iso_19011.pdf")),
)

__all__ = ["BUNDLES", "Bundle", "BundleError"]
