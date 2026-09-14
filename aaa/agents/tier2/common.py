"""Helpers shared by the Tier-2 phase agents."""
from __future__ import annotations

from typing import Any

from aaa.platform.evidence import EvidenceStore


def load_intake(store: EvidenceStore, evidence_uris: list[str]) -> tuple[dict, dict]:
    """Load the T01a triage and T01b Annex IV dossier from the Evidence Store.

    Artefacts are recognised by their characteristic fields rather than by
    URI naming, so re-ordered dispatch lists still resolve correctly.

    :param store: Evidence store to read from.
    :param evidence_uris: Candidate artefact URIs from the dispatch.
    :returns: ``(t01a, t01b)`` dictionaries — empty when not found.
    """
    t01a: dict[str, Any] = {}
    t01b: dict[str, Any] = {}
    for uri in evidence_uris:
        content = store.get_artefact(uri)
        if content is None:
            continue
        if "declared_modality" in content or "provider_name" in content:
            t01a = content
        elif "general_description" in content or "model_type" in content:
            t01b = content
    return t01a, t01b
