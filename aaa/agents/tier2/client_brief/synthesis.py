"""The brief's opening pass: why the audit landed where it did, and what held up."""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier2.client_brief.constants import PROMPT_NAME
from aaa.agents.tier2.client_brief.overview import _overview_payload, deterministic_overview
from aaa.tools.evidence_retrieval import acompletion_json_react

logger = logging.getLogger(__name__)

_CONTRACT: tuple[str, ...] = ("overall_explanation", "what_is_working_well")

#: Prose keys the renderer prints from the overview, in order.
OVERVIEW_KEYS: tuple[str, ...] = (
    "overall_explanation", "what_is_working_well", "what_is_blocking_the_verdict",
    "what_could_not_be_checked", "top_priorities",
)






async def write_overview(agent: Any, state: dict[str, Any],
                         sections: list[dict[str, Any]]) -> dict[str, Any]:
    """Compose the brief's opening, falling back to state alone on failure.

    :param agent: The calling :class:`ClientBriefAgent`.
    :param state: Final ``AuditState``.
    :param sections: The per-article sections already written.
    :returns: The overview payload, flagged with ``llm_written``.
    """
    try:
        payload = await acompletion_json_react(
            agent, PROMPT_NAME, _overview_payload(state, sections),
            contract=_CONTRACT, rounds=0)
    except Exception as exc:  # noqa: BLE001 — the brief ships without a written opening
        logger.warning("Client brief: overview fell back to the deterministic "
                       "assembly (%s).", exc)
        return deterministic_overview(state)
    return {**{k: payload[k] for k in OVERVIEW_KEYS if payload.get(k)},
            "llm_written": True}
