"""What killed a phase attempt, classified so the finding can name the right cause."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.phases.verification.logger import _REPORT_TIDS

#: The pseudo-verdict of an artefact that was never produced. It sits beside the
#: real verdicts in ``unadmitted_artefacts`` so one reader — the matrix, the T18
#: manifest, the HITL packet — sees every reason an article went unevidenced in
#: one list, rather than having to know about a second one.
NO_REPORT: str = "no report"

#: Where ``run_agent_on_state`` leaves what it caught, for the gate to read.
FAILURE_KEY: str = "_last_phase_failure"

_TIMEOUT_NAMES = ("TimeoutError", "Timeout", "CancelledError")


def record_phase_failure(state: dict, agent_name: str, elapsed: float,
                         timeout: float | None, exc: BaseException) -> None:
    """Leave what killed the attempt where :func:`gate_on_no_report` can read it.

    :param state: The mutable AuditState dict.
    :param agent_name: ``BaseAgent.name`` of the agent that failed.
    :param elapsed: Wall-clock seconds the attempt ran before it gave up.
    :param timeout: The budget it was given, if one was applied.
    :param exc: The exception ``run_agent_on_state`` caught.
    """
    state[FAILURE_KEY] = {
        "agent": agent_name, "elapsed_s": round(elapsed, 1),
        "timeout_s": timeout, "error": repr(exc)[:400],
        "kind": _classify(exc),
    }


def _classify(exc: BaseException) -> str:
    """Name the failure class, so the finding can attribute it to the right fix."""
    from aaa.platform.transient_retry import is_transient

    name = type(exc).__name__
    if any(t in name for t in _TIMEOUT_NAMES):
        return "budget"
    if is_transient(exc):
        return "provider"
    return "error"


def _cause(failure: dict[str, Any]) -> str:
    """One clause a reader can act on, naming which failure this was.

    A missing record is itself stated rather than guessed at. It should not
    happen — ``run_agent_on_state`` writes one for every exception it catches —
    and inventing a cause for a phase that produced nothing would be the exact
    class of defect this fix removes.
    """
    kind, elapsed, budget = (failure.get("kind"), failure.get("elapsed_s"),
                             failure.get("timeout_s"))
    if kind == "budget":
        return (f"the phase was abandoned at its {budget:.0f}s budget"
                if budget else "the phase exceeded its wall-clock budget")
    if kind == "provider" and elapsed is not None:
        return (f"the provider failed after {elapsed:.1f}s and the failure survived "
                f"its retry")
    if kind and elapsed is not None:
        return f"the agent raised after {elapsed:.1f}s: {failure.get('error', '')[:200]}"
    return "the agent produced no report and no cause was recorded"


def _entries(tid_articles: dict[str, list[str]], failure: dict[str, Any], *,
             phase_id: str, phase_label: str) -> list[dict[str, Any]]:
    """One ``unadmitted_artefacts`` record per artefact the phase never produced."""
    reason = _cause(failure)
    return [{"phase_id": phase_id, "phase_label": phase_label, "template_id": tid,
             "verdict": NO_REPORT,
             "articles": [] if tid in _REPORT_TIDS else list(articles),
             "reason": reason}
            for tid, articles in tid_articles.items()]


__all__ = ["FAILURE_KEY", "NO_REPORT", "_cause", "_classify", "_entries",
           "record_phase_failure"]
