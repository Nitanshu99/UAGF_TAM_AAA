"""Classify an AI system against the Annex III high-risk use cases."""
from __future__ import annotations

from aaa.platform.state import AnnexIIIEntry
from aaa.tools.annex_iii_classify.evidence import section_evidence
from aaa.tools.annex_iii_classify.make_entry import _resolve_entry
from aaa.tools.annex_iii_classify.points import POINTS

_PROVENANCE_ORDER = {"client_declared": 0, "phase1_verified": 1,
                     "phase1_corrected": 2, "phase1_rejected": 3}


def annex_iii_classify(declared_sections: list[str],
                       system_description: str) -> list[AnnexIIIEntry]:
    """Classify a system against Annex III from its own intake text.

    :param declared_sections: Sections the provider declared in Stage A.
    :param system_description: Intended purpose, general description and data
        description — the only evidence the classifier reads.
    :returns: One entry per declared section and per undeclared section with
        enough evidence, declared first, then by confidence.
    """
    text = system_description.lower()
    declared = {str(s) for s in declared_sections}
    entries = [entry for section in POINTS
               if (entry := _resolve_entry(section, section_evidence(section, text),
                                           section in declared)) is not None]
    entries.sort(key=lambda e: (_PROVENANCE_ORDER.get(e["provenance"], 9), -e["confidence"]))
    return entries


__all__ = ["annex_iii_classify"]
