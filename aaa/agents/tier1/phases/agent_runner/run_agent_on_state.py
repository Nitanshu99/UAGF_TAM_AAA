"""Part 3 of the former ``agent_runner`` module (auto-split)."""
from __future__ import annotations

import time
from typing import Any

from aaa.agents.tier1.phases.agent_runner.apply_delta import _apply_delta  # noqa: F401
from aaa.agents.tier1.phases.agent_runner.dedup_accumulated import _dedup_accumulated  # noqa: F401
from aaa.agents.tier1.phases.agent_runner.logger import (  # noqa: F401
    _ACCUMULATE_KEYS,
    _evidence_uris,
    _invoke,
    logger,
)
from aaa.platform.phase_budget import phase_timeout


async def run_agent_on_state(
    agent: Any,
    dispatch: Any,
    state: dict,
    timeout: int | None = None,
    spawn: str | None = None,
) -> tuple[Any, dict]:
    """Run *agent* with *dispatch*, apply delta to *state*, return (report, state).

    Returns (None, state) if the agent raises an exception — callers
    can fall back to stub behaviour.

    :param timeout: Seconds the agent is allowed. ``None`` — the default since
        fix 34 — derives it from what this agent's calls have just cost, which
        is the only reading that stays true when the provider changes; the
        literal it replaced (180 s, 120 s for Phase 1) rested on a measurement
        nothing ever took again and cost four of five cases their Phase 1 (R1).
    :param spawn: Set by a tier-3 spawn to name the namespace its artefacts land
        in, so the spawn cannot displace the tier-2 template it extends (P5).
        Phases pass nothing and keep replacing their own artefacts on a rerun.
    """
    if timeout is None:
        timeout = phase_timeout(getattr(agent, "name", None))
    started = time.monotonic()
    try:
        report = await _invoke(agent, dispatch, timeout)
        delta = report.get("declaration_verification_delta", {})
        _apply_delta(state, delta, spawn)
        return report, state
    except Exception as exc:
        # Fix 35: three different findings produce the one symptom "no report",
        # and only here is the evidence that tells them apart still in hand.
        # The gate reads it to say *which* failure this was. Imported lazily:
        # `verification` imports this module, so a module-level import here
        # closes the cycle and rebinds `run_agent_on_state` to its package.
        from aaa.agents.tier1.phases.verification.no_report import record_phase_failure
        record_phase_failure(state, getattr(agent, "name", type(agent).__name__),
                             time.monotonic() - started, timeout, exc)
        # `TimeoutError` and `CancelledError` carry no message, so `%s` alone
        # logged "failed after 300.0s ()" — which says a phase was abandoned but
        # not what abandoned it, and three artefacts were withheld on the
        # strength of it. Name the type whenever the message is empty.
        detail = str(exc) or type(exc).__name__
        logger.warning(
            "%s.process() failed after %.1fs of a %.0fs budget (%s); the phase "
            "produced no report.",
            type(agent).__name__, time.monotonic() - started, timeout, detail,
        )
        return None, state


__all__ = ["run_agent_on_state", "_evidence_uris"]
