"""Which model one call may fall back to once its own transient retries are spent.

User decision (2026-09-13): on the free route, a call that exhausts its retries
against nemotron-3-ultra:free is retried — that call only — against
nemotron-3-super:free, with its own retries. The run's model never changes; the
audit row records which model answered. A mapping, not a rule, so a pinned paid
endpoint is never silently swapped for another model.
"""
from __future__ import annotations

import os

#: Primary model → the free fallback one exhausted call may use.
FALLBACK_MODELS: dict[str, str] = {
    "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free":
        "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
}


def fallback_model_for(model: str) -> str | None:
    """The fallback for *model*, or ``None``; ``AAA_TRANSIENT_FALLBACK=off`` disables all.

    :param model: The LiteLLM model string the call was made with.
    """
    if os.environ.get("AAA_TRANSIENT_FALLBACK", "").strip().lower() in {"off", "0", "false"}:
        return None
    return FALLBACK_MODELS.get(model)


__all__ = ["FALLBACK_MODELS", "fallback_model_for"]
