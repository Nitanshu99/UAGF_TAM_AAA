"""LLM synthesis for Phase 6 with deterministic fallback."""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier2.report_architect.constants import PROMPT_NAME
from aaa.agents.tier2.tools_run import tools_run
from aaa.tools.evidence_retrieval import acompletion_json_react

logger = logging.getLogger(__name__)


def _reject_claimed_signature(payload: dict[str, Any]) -> None:
    """Log a model-asserted ``report_signed`` before it is discarded (F15).

    The runtime derives the signature from the report it actually produced
    (``report_architect.signing``).  The model's claim is not evidence of
    anything, but a claim on empty content is worth seeing in the trail —
    at case 01 call #035 it was made beside an empty summary and URI.
    """
    if payload.get("report_signed"):
        logger.error(
            "ReportArchitect asserted report_signed=%r; discarded — the "
            "signature is derived by the runtime, never claimed by the model.",
            payload.get("report_signed"))


async def run_llm_synthesis(
    agent: Any,
    message: dict[str, Any],
    decl: dict[str, Any],
    t17: dict[str, Any],
    t18: dict[str, Any],
) -> tuple[str | None, str]:
    """Ask the LLM to compose the executive summary and refine the opinion.

    Falls back to the deterministic T18 assembly when the call fails — which
    now includes the model answering with a ``retrieval_plan`` instead of a
    report (F15).  Phase 6 composes from admitted artefacts and has no
    retrieval channel of its own, so ``rounds=0``: the call is single-shot and
    a plan-shaped reply is refused rather than filed as the report.  A returned
    ``auditor_opinion`` dict is merged into *t18* in place.

    :param agent: The calling :class:`ReportArchitect` instance.
    :param message: Original dispatch message.
    :param decl: Declaration summary from the dispatch.
    :param t17: T17 compliance-matrix payload.
    :param t18: T18 payload; mutated when the LLM refines the opinion.
    :returns: ``(llm_summary, prompt_note)``.
    """
    fallback = True
    llm_summary: str | None = None
    try:
        payload = await acompletion_json_react(
            agent, PROMPT_NAME,
            {"task": message.get("task_brief")
             or "Compose the final T18 audit report from admitted artefacts.",
             "evidence_uris": message.get("evidence_uris", []),
             "declaration_summary": decl,
             "t17_payload": t17,
             "t18_seed": t18,
             "tools_executed": tools_run("P6")},
            # Fix 42: the keys this caller reads below are its output
            # contract, asserted at the answer position instead of
            # discovered as an empty `.get()` after the reply is filed.
            contract=("executive_summary", "summary", "rationale_summary"),
            rounds=0)
        _reject_claimed_signature(payload)
        llm_summary = (payload.get("executive_summary")
                       or payload.get("summary")
                       or payload.get("rationale_summary"))
        if isinstance(payload.get("auditor_opinion"), dict):
            t18["auditor_opinion"].update(payload["auditor_opinion"])
        fallback = False
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("ReportArchitect prompt runtime failed (%s); "
                       "using deterministic fallback.", exc)
    return llm_summary, agent.prompt_note(PROMPT_NAME, fallback)
