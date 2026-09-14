"""Mapping the LLM's verdict word onto the five verdict codes this system acts on."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.verifier.issues import (
    _ADMITTING,
    material_non_conformity,
    rests_on_provider_issues,
)
from aaa.agents.tier1.verifier.verdicts import MAX_RERUNS, VerifierVerdict, decide_verdict, logger


def _verdict_code(raw_verdict: Any, issues: list[dict[str, Any]], notes: list[str],
                  rerun_count: int) -> VerifierVerdict:
    """Translate the model's verdict string, falling back to the rubric ladder.

    :param raw_verdict: The model's verdict string.
    :param issues: Normalised issue records.
    :param notes: The model's notes.
    :param rerun_count: Reruns already consumed for this artefact.
    :returns: The verdict code, before the materiality gate.
    """
    if isinstance(raw_verdict, str):
        verdict = raw_verdict.strip().upper()
        if verdict == "ACCEPT":
            return "accept"
        if verdict == "ACCEPT_WITH_OBSERVATIONS":
            return "accept_with_notes"
        if verdict == "RERUN":
            return "rerun" if rerun_count < MAX_RERUNS else "escalate_hitl"
        if verdict == "ESCALATE_HITL":
            return "escalate_hitl"
    return decide_verdict(issues, notes, rerun_count)
def _map_llm_verdict(raw_verdict: Any, issues: list[dict[str, Any]], notes: list[str],
                     rerun_count: int, scores: dict | None = None) -> VerifierVerdict:
    """Map the model's verdict string onto the verdict ladder (with fallback).

    An admitting verdict is refused where the model has itself recorded a
    confirmed material non-conformity (M2). This enforces the prompt's own rule
    rather than adding a policy to it — ``PROMPT.md`` reserves ``ESCALATE_HITL``
    for exactly two cases, ``factual_accuracy = 0`` *or* "a confirmed
    **material** non-conformity", and at call #040 of the 2026-09-10 Mariposa
    run the model returned ``ACCEPT_WITH_OBSERVATIONS`` on ``T10`` while
    recording two issues at ``severity: critical, materiality: material``. Both
    cannot be true: either the artefact is not evidence, or the materiality is
    wrong. Only the five-dimension total was read, so both stood.

    It escalates rather than re-running (M20). That is what the rule says —
    ``ESCALATE_HITL`` is *for* a confirmed material non-conformity — and the
    2026-09-10 verification run measured the alternative: of thirteen gated
    artefacts sent round the rerun ladder first, **none** was repaired. A
    two-sample golden set and an undeclared special category are not re-writing
    problems, so the two attempts bought nothing and cost two critiques each.

    :param raw_verdict: The model's verdict string.
    :param issues: Normalised issue records, read for materiality.
    :param notes: The model's notes, used only by the fallback ladder.
    :param rerun_count: Reruns already consumed for this artefact.
    :returns: The verdict code.
    """
    verdict = _verdict_code(raw_verdict, issues, notes, rerun_count)
    if verdict not in _ADMITTING:
        # A rejection that rests only on what the artefact records about the provider
        # is not a rejection of the artefact; those issues go to the matrix (option A).
        if verdict in ("rerun", "escalate_hitl") and rests_on_provider_issues(issues, scores):
            logger.info("Verifier returned %r on provider findings only; the artefact is "
                        "admitted and the findings are carried to the matrix.", verdict)
            return "accept_with_notes"
        return verdict
    blocker = material_non_conformity(issues)
    if blocker is None:
        return verdict
    logger.warning(
        "Verifier returned %r while recording a confirmed material "
        "non-conformity on %r (%s); escalating to human review.",
        verdict, blocker.get("field") or "the artefact",
        str(blocker.get("description") or "")[:160])
    return "escalate_hitl"


__all__ = ["_map_llm_verdict", "_verdict_code"]
