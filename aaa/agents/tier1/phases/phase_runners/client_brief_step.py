"""Phase 6's closing step: write the customer's brief from the finished state.

Runs after the ReportArchitect, not beside it, because it needs what that agent
produced — the auditor's opinion and the final verdict reach the state only when
Phase 6's report is applied. It is also the last thing the run does, so a
failure here loses a deliverable and nothing else; the audit itself is already
concluded and stored.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.base import Dispatch
from aaa.agents.tier1.phases.agent_runner import run_agent_on_state
from aaa.agents.tier1.phases.phase_runners.logger import logger


def brief_timeout(state: dict) -> int:
    """Seconds the brief needs: one call per audited article, plus the opening.

    The standard phase budget funds two LLM calls, which is what a phase agent
    makes. This agent makes one per requirement — eighteen on a full high-risk
    engagement — so it is sized from the same measured per-call cost times the
    number of calls it will actually make.

    :param state: Final ``AuditState``.
    :returns: Whole seconds.
    """
    from aaa.agents.tier2.client_brief import audited_articles
    from aaa.platform.phase_budget import CALLS_PER_PHASE, phase_timeout
    per_call = phase_timeout("ClientBrief") / CALLS_PER_PHASE
    return int(per_call * (len(audited_articles(state)) + 1))


async def run_client_brief(agent: Any, state: dict) -> dict:
    """Write and store the plain-language client brief for this engagement.

    :param agent: The ``ClientBriefAgent``, or ``None`` when unwired.
    :param state: Final ``AuditState``, after Phase 6 has been applied.
    :returns: *state*, with ``phase_artefacts["T19_client_brief"]`` registered
        when the brief was written.
    """
    eng = state["engagement_id"]
    if agent is None:
        logger.warning(
            "Engagement %s: no ClientBrief agent is wired, so the customer "
            "receives the formal report with no plain-language brief beside it.",
            eng)
        return state
    dispatch = Dispatch(
        phase_id="P6",
        task_brief="Rewrite the concluded audit for the customer, article by article.",
        evidence_uris=[],
        output_contract="T19_client_brief",
        # The brief reasons over the whole final state: declarations, admitted
        # and rejected artefacts, findings and the matrix. A projection of it
        # would decide in advance which contradictions the brief can name.
        declaration_summary=state,
    )
    report, state = await run_agent_on_state(agent, dispatch, state,
                                             timeout=brief_timeout(state))
    if report is None:
        logger.error("Engagement %s: the client brief was not produced; the "
                     "formal report and its evidence are unaffected.", eng)
    else:
        logger.info("Engagement %s: client brief stored at %s.",
                    eng, report["artefact_uri"])
    return state
