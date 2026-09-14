"""The three ways a run degrades: stub artefacts, fallback critiques, and degraded phases."""
from __future__ import annotations

from typing import Any, Final

from aaa.platform.state.artefact_keys import base_template_id
from aaa.tools.regulatory_coverage.ownership import TEMPLATE_PHASE

#: The ``sha256`` a stub artefact carries. Written by exactly one function —
#: ``aaa.agents.tier1.phases.node_stubs.logger._stub_artefact`` — so a match is
#: proof of a placeholder rather than a heuristic about the URI scheme.
STUB_SHA: Final = "stub"
def stub_artefact_ids(state: dict[str, Any]) -> list[str]:
    """Artefact keys in *state* whose payload is a deterministic placeholder.

    :param state: Audit state carrying ``phase_artefacts``.
    :returns: Sorted artefact keys, spawn namespaces preserved.
    """
    artefacts = state.get("phase_artefacts") or {}
    return sorted(key for key, ref in artefacts.items()
                  if isinstance(ref, dict) and ref.get("sha256") == STUB_SHA)
def fallback_critique_ids(state: dict[str, Any]) -> list[str]:
    """Artefacts admitted on a critique the Verifier's *model* never wrote.

    The Verifier is the integrity gate, and it fails soft: when its call cannot
    be made it falls back to a deterministic rubric that "returns a verdict
    looking exactly like a real one"
    (:mod:`aaa.agents.tier1.verifier.fallback`). That verdict is a placeholder
    in precisely the sense this module was written for — indistinguishable to a
    consumer from an independently judged one.

    ``stub_artefact_ids`` could not see it. On 2026-09-09 a Mariposa run lost
    its provider mid-engagement (34 of 54 calls failing through ``429`` → ``503``
    → ``404``), produced a report whose every narrative section had fallen back,
    left **10 of 17** critiques authored by the rubric — and was still stamped
    ``suitable_for_handoff: True``, because it wrote no stub. A healthy run of
    the same case carries zero.

    Scope, stated plainly: this reads the Verifier's own record, which is the
    fallback signal that reaches ``AuditState``. A phase agent's fallback is
    noted in its artefact narrative (``llm_fallback_mode`` in the prompt note),
    which lives in the evidence store rather than here, so it is not counted.
    An unverified run is the stronger signal anyway: it means nothing checked
    the artefact, whoever wrote it.

    :param state: Audit state carrying ``verifier_critiques``.
    :returns: Sorted template ids whose critique was not independently authored.
    """
    critiques = state.get("verifier_critiques") or {}
    return sorted(
        tid for tid, critique in critiques.items()
        if isinstance(critique, dict)
        and (critique.get("llm_fallback_mode") or critique.get("verdict") == "unverified"))
def degraded_phases(state: dict[str, Any]) -> list[str]:
    """Phases that delivered a placeholder in place of an artefact.

    The *owning* phase is reported, not every phase that may extend the
    template: a stub is written by the phase runner whose dispatch was skipped,
    so ``T11_robustness_report`` degrades P3 even though CYBER also emits it.

    :param state: Audit state carrying ``phase_artefacts``.
    :returns: Sorted phase ids, e.g. ``["P1", "P5"]``.
    """
    phases = set()
    for key in stub_artefact_ids(state):
        owners = TEMPLATE_PHASE.get(base_template_id(key))
        phases.add(owners[0] if owners else "UNKNOWN")
    return sorted(phases)
def is_degraded(state: dict[str, Any]) -> bool:
    """Whether *state* holds any placeholder artefact.

    Computed from ``phase_artefacts`` rather than read from a stamped block, so
    it answers correctly mid-run — before the customer writer has stamped
    anything — as well as for a delivered file.

    :param state: Audit state carrying ``phase_artefacts``.
    :returns: True when at least one artefact is a stub.
    """
    return bool(stub_artefact_ids(state))


__all__ = ["STUB_SHA", "degraded_phases", "fallback_critique_ids", "is_degraded", "stub_artefact_ids"]
