"""Critique-record shaping for the Verifier LLM path."""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier1.verifier.issues import _normalise_issues
from aaa.agents.tier1.verifier.verdict_codes import _map_llm_verdict

logger = logging.getLogger(__name__)


def _reconcile_rerun_flag(raw: dict, verdict: str, notes: list) -> list:
    """Record a model-asserted ``rerun_required`` that its verdict contradicts.

    The two fields are set independently in the reply and instruct the runtime
    to do opposite things — admit the artefact, and re-dispatch the phase. The
    verdict is authoritative and the flag is derived from it, which is right;
    what was wrong is that the disagreement vanished (M3). At calls #021 and
    #048 of the 2026-09-10 Mariposa run the model returned
    ``ACCEPT_WITH_OBSERVATIONS`` with ``rerun_required: true`` and nothing
    recorded that it had asked for a rerun.

    Same treatment as a model-asserted ``report_signed`` (F15) and an invented
    ``artefact_uri`` (F20): the claim is discarded, and never quietly.

    :param raw: The parsed model reply.
    :param verdict: The verdict the ladder resolved to.
    :param notes: The model's notes, not mutated.
    :returns: The notes, with the discard recorded when there was one.
    """
    if not bool(raw.get("rerun_required")) or verdict == "rerun":
        return notes
    logger.warning(
        "Verifier set rerun_required=true alongside verdict %r; the verdict is "
        "authoritative and the flag is discarded, but the disagreement is "
        "recorded on the critique.", verdict)
    return [*notes,
            f"The Verifier returned rerun_required=true with verdict '{verdict}'. "
            f"The verdict governs; the rerun request is recorded, not actioned."]


def _result(phase_id: str, template_id: str, raw: dict, rerun_count: int,
            agent: Any) -> dict[str, Any]:
    """Shape the parsed model reply into the stored critique record."""
    issues = _normalise_issues(raw.get("issues", []))
    notes = raw.get("notes", [])
    verdict = _map_llm_verdict(raw.get("verdict"), issues, notes, rerun_count,
                               raw.get("scores") if isinstance(raw.get("scores"), dict) else None)
    return {
        "phase_id": phase_id,
        "template_id": template_id,
        "verdict": verdict,
        "issues": issues,
        "notes": _reconcile_rerun_flag(raw, verdict, list(notes or [])),
        "article_citations": raw.get("article_citations", []),
        "scores": raw.get("scores", {}),
        "total_score": raw.get("total_score"),
        "materiality_assessments": raw.get("materiality_assessments", []),
        "declaration_mismatches": raw.get("declaration_mismatches", []),
        "llm_fallback_mode": False,
        "prompt_metadata": agent.prompt_metadata("verifier", False),
        "rerun_required": verdict == "rerun",
    }
