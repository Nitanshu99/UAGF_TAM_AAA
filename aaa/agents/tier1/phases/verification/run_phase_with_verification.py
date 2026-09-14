"""The phase loop: run the agent, critique what it produced, honour the verdict."""
from __future__ import annotations

import time
from typing import Any

from aaa.agents.tier1.phases.agent_runner import run_agent_on_state
from aaa.agents.tier1.phases.verification.close import close_phase
from aaa.agents.tier1.phases.verification.confidence import read_confidence
from aaa.agents.tier1.phases.verification.logger import _get_verifier, logger
from aaa.agents.tier1.phases.verification.lost_attempt import record_lost_attempt
from aaa.agents.tier1.phases.verification.rerun import apply_rerun_context, rerun_requested
from aaa.agents.tier1.phases.verification.verify_artefacts import _verify_artefacts
from aaa.agents.tier1.verifier import MAX_RERUNS


async def run_phase_with_verification(
    agent: Any, dispatch: Any, state: dict,
    tid_articles: dict[str, list[str]], phase_label: str,
    *, timeout: int | None = None, default_confidence: float = 0.9,
) -> tuple[Any, dict]:
    """Run *agent*, critique each artefact with the real Verifier, honour the verdict.

    Returns ``(report, state)``; ``report`` is ``None`` if the agent failed (caller
    falls back to its stub). When **any** artefact carries a ``rerun`` verdict the
    agent is re-dispatched up to ``MAX_RERUNS`` times, carrying the critique that
    ordered it; an unresolved ``rerun`` or ``escalate_hitl`` flags HITL.

    Since fix 32 this loop is the *only* re-dispatch of a phase that produced an
    artefact. The Orchestrator dispatches a phase that has delivered nothing; a
    delivered artefact the Verifier rejected is re-run here, where the critique,
    the rerun budget and the re-critique all are.
    """
    verifier = _get_verifier(getattr(agent, "rag", None))
    rerun_count = 0
    phase_id = dispatch.get("phase_id", "") if isinstance(dispatch, dict) else ""
    # Fix 34: `timeout=None` — what every caller now passes — is *derive it*,
    # and the derivation lives one level down in `run_agent_on_state` so that a
    # rerun re-derives rather than inheriting attempt 1's number: by then the
    # process has watched attempt 1 and knows more than it did. `phase_timeout`
    # logs the reading it used (finding R1).
    logger.info("%s: started (agent dispatch, timeout=%s).", phase_label,
                f"{timeout}s" if timeout else "derived from measured latency")
    t_phase = time.monotonic()
    while True:
        t_agent = time.monotonic()
        report, state = await run_agent_on_state(agent, dispatch, state, timeout=timeout)
        if report is None:
            record_lost_attempt(state, tid_articles, t_agent,
                                phase_id=phase_id, phase_label=phase_label,
                                rerun_count=rerun_count)
            return None, state
        logger.info("%s: agent complete in %.1fs; running Verifier on %d artefact(s).",
                    phase_label, time.monotonic() - t_agent, len(tid_articles))
        # F5: `float(report.get(..., default) or default)` read a reported 0.0
        # as the 0.9 default — an agent saying it was not confident was recorded
        # as highly confident. `default_confidence` applies only when the agent
        # reported no value at all.
        confidence = read_confidence(report, default_confidence, phase_label)

        worst = await _verify_artefacts(
            verifier, agent, dispatch, state, tid_articles,
            phase_label, confidence, rerun_count)

        # Q8 / fix 32: asked per artefact, not of the phase's worst verdict. A
        # `rerun` masked by a sibling's `escalate_hitl` used to be dropped here
        # and picked up by the Orchestrator re-dispatching the whole phase —
        # two mechanisms for one job, and the slower one had no rerun_context.
        if rerun_requested(state, list(tid_articles)) and rerun_count < MAX_RERUNS:
            rerun_count += 1
            apply_rerun_context(state, dispatch, list(tid_articles),
                                rerun_count, phase_label)
            continue
        close_phase(state, report, tid_articles, confidence, worst,
                    rerun_count=rerun_count, t_phase=t_phase,
                    phase_id=phase_id, phase_label=phase_label,
                    load=getattr(getattr(agent, "store", None), "get_artefact", None))
        return report, state


__all__ = ["run_phase_with_verification"]
