"""Timing one model call in the ReAct retrieval loop, and logging what it cost."""
from __future__ import annotations

import time
from typing import Any


async def _timed(agent: Any, prompt_name: str, payload: dict[str, Any],
                 costs: list[float]) -> Any:
    """Invoke the model and record what the call cost.

    Fix 18's deadline gate estimates the next round from the calls already made,
    so every call in this loop has to be measured — the estimate is a reading of
    this model on this payload, not a constant.

    :param agent: The phase agent.
    :param prompt_name: PROMPT.md section name.
    :param payload: The user payload.
    :param costs: Accumulator of per-call wall-clock seconds; appended to.
    :returns: The model's parsed reply.
    """
    started = time.monotonic()
    try:
        return await agent.acompletion_json(prompt_name, payload)
    finally:
        costs.append(time.monotonic() - started)


__all__ = ["_timed"]
