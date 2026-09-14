"""Carrying the critique that ordered a rerun into the re-dispatched agent's brief."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.phases.verification.logger import logger
from aaa.agents.tier1.phases.verification.rerun_context import build_rerun_context, rerun_requested
from aaa.agents.tier1.verifier import MAX_RERUNS


def apply_rerun_context(state: dict, dispatch: Any, tids: list[str],
                        rerun_count: int, phase_label: str) -> None:
    """Attach the rejected artefacts' critiques to *dispatch* before the rerun.

    F2: without this the agent is re-asked the identical question and told
    nothing about why its answer was rejected.

    :param state: The AuditState dict, holding the critiques.
    :param dispatch: The dispatch about to be re-sent; mutated in place.
    :param tids: Template ids this phase was contracted to emit.
    :param rerun_count: Which rerun this is (1-based).
    :param phase_label: Human-readable phase label used in the logs.
    """
    context = build_rerun_context(state, tids, rerun_count)
    if isinstance(dispatch, dict):
        dispatch["rerun_context"] = context
    else:
        logger.warning("%s: dispatch is not a dict; rerun_context dropped.",
                       phase_label)
    logger.info(
        "%s: verifier requested rerun (%d/%d); re-dispatching with "
        "%d rejected artefact(s) in rerun_context.",
        phase_label, rerun_count, MAX_RERUNS, len(context["rejected_artefacts"]))


__all__ = ["apply_rerun_context", "rerun_requested"]
