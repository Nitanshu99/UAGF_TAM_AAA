"""The artefact URI the evidence store issued, never the one the model asserted."""
from __future__ import annotations

from aaa.agents.tier1.phases.verification.logger import _artefact_uri, logger


def _resolved_artefact_uri(state: dict, rep: dict, tids: list[str],
                           phase_label: str) -> str:
    """The URI the store actually issued, never the one the model asserted.

    Every tier-2 phase agent in the 2026-09-09 Mariposa run invented this field,
    and the tells are unmistakable: ``T02_system_card_a1b2c3d4.json`` beside
    ``_e5f6g7h8`` and ``_i9j0k1l2`` (call #004), one hash shared by three
    artefacts that are each content-hashed separately (#022), a ``_v2`` suffix
    (#026), a ``_20250115`` date stamp in the wrong year (#036), and no hash at
    all (#043). The tier-3 agents did not: #048 and #050 both extended a *real*
    hash they had been given, which is what makes this a prompt-and-enforcement
    gap rather than a model limitation.

    The Verifier was never fooled — it critiques through
    :func:`_artefact_uri`, which reads ``phase_artefacts``. This field is the
    one that travelled: ``latest_report`` is handed to the Orchestrator on every
    subsequent turn, so a dangling URI was being presented to the planner as the
    evidence its next decision rests on.

    Same treatment as a model-asserted ``report_signed`` (F15) and a
    ``tool_calls`` entry naming a tool that never ran (F10): the claim is
    discarded, and never quietly.

    :param state: AuditState carrying ``phase_artefacts``.
    :param rep: The phase agent's Report.
    :param tids: Template ids this phase was contracted to emit.
    :param phase_label: Human-readable phase label, for the log line.
    :returns: The stored URI for the phase's first contracted artefact, or
        ``""`` when nothing was stored.
    """
    stored = [uri for uri in (_artefact_uri(state, tid) for tid in tids) if uri]
    claimed = str(rep.get("artefact_uri") or "")
    # A claim naming *any* of this phase's stored artefacts is the agent's own
    # choice of primary deliverable, and it is better informed than position in
    # `tids`. Insisting on ``tids[0]`` overwrote a correct answer: Phase 6 emits
    # T17 then T18 and reports T18, so this replaced a real T18 URI with T17's
    # and logged a fabrication warning against an honest report.
    if claimed and claimed in stored:
        return claimed
    if claimed:
        logger.warning(
            "%s: the agent reported artefact_uri=%r, which the evidence store "
            "never issued for this phase; recording %r instead. The URI is "
            "assigned by template_render, not chosen by the model.",
            phase_label, claimed, stored[0] if stored else "<nothing stored>")
    return stored[0] if stored else ""


__all__ = ["_resolved_artefact_uri"]
