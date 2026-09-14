"""Finding Q9 — a cost column reading 0.0000 asserts the run was free.

Every one of the 48 records in the part-2 run carried
``estimated_cost_usd: 0.0000``.  Nothing was measured: ``litellm.completion_cost``
returns zero for a model absent from its cost map, and every ``nvidia_nim/*``
identifier is absent from it — ``ModelConfig`` already says so in its own
docstring, one field over.  The run happened to be on a free-tier account, so the
number was right by accident; on a paid deployment the same code would report the
same 0.0000 and the audit trail would understate what the engagement cost.

Zero and *unknown* are different statements, and this file's job is to keep them
apart.  A price that cannot be established is recorded as ``null`` with
``cost_basis: "unpriced"``, never as a number.

**No prices are hard-coded here, and that is deliberate.** NIM pricing varies by
contract, region and tier, and a guessed rate written into a trail a client may
rely on would be exactly the class of defect this document has spent thirty-odd
fixes removing. The rates come from the operator, through
``MODEL_PRICES_USD_PER_1M``, and a call priced from them is recorded
``cost_basis: "declared"`` so a reader knows whose number it is. An operator on
the free tier declares zeros explicitly, and the trail then says *that* rather
than saying nothing and meaning zero.

``MODEL_PRICES_USD_PER_1M`` is JSON, USD per million tokens::

    MODEL_PRICES_USD_PER_1M={"nvidia_nim/nvidia/nemotron-3-ultra-550b-a55b":
                             {"input": 0.0, "output": 0.0}}
"""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

#: Cost basis recorded beside the number, so a reader knows where it came from.
LITELLM, DECLARED, UNPRICED = "litellm", "declared", "unpriced"

_PER_MILLION = 1_000_000.0


def declared_prices() -> dict[str, dict[str, float]]:
    """Parse the operator's declared per-model rates, or ``{}``.

    :returns: ``{model: {"input": usd_per_1m, "output": usd_per_1m}}``.
    """
    from aaa.settings import settings

    raw = str(getattr(settings, "model_prices_usd_per_1m", "") or "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError) as exc:
        logger.warning("MODEL_PRICES_USD_PER_1M is not valid JSON (%s); "
                       "calls will be recorded unpriced.", exc)
        return {}
    if not isinstance(parsed, dict):
        logger.warning("MODEL_PRICES_USD_PER_1M must be an object keyed by model "
                       "id, got %s; calls will be recorded unpriced.",
                       type(parsed).__name__)
        return {}
    return {str(model): {"input": float(rates.get("input", 0.0)),
                         "output": float(rates.get("output", 0.0))}
            for model, rates in parsed.items() if isinstance(rates, dict)}


def _from_litellm(response: Any) -> float | None:
    """Ask LiteLLM to price the call; ``None`` when it has no rate for the model.

    A zero from LiteLLM is treated as *no rate*, because that is what it means
    for the roster this system runs: the model is not in its cost map.
    """
    try:
        import litellm  # type: ignore

        cost = litellm.completion_cost(completion_response=response)
    except Exception:  # noqa: BLE001 — pricing must never fail a call
        return None
    return float(cost) if cost else None


def resolve_cost(response: Any, model: str,
                 usage: dict[str, int] | None = None) -> tuple[float | None, str]:
    """Price one call and say where the price came from.

    :param response: The provider's response object.
    :param model: The model identifier the call was made against.
    :param usage: Token counts for this call, when already extracted.
    :returns: ``(cost_usd or None, cost_basis)``.
    """
    cost = _from_litellm(response)
    if cost is not None:
        return round(cost, 6), LITELLM

    rates = declared_prices().get(model)
    if rates is None:
        return None, UNPRICED
    tokens = usage or {}
    declared = (rates["input"] * int(tokens.get("prompt_tokens", 0) or 0)
                + rates["output"] * int(tokens.get("completion_tokens", 0) or 0))
    return round(declared / _PER_MILLION, 6), DECLARED


__all__ = ["LITELLM", "DECLARED", "UNPRICED", "declared_prices", "resolve_cost"]
