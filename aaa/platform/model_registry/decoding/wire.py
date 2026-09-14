"""What actually reaches the provider, which is not always what was asked for.

``drop_params`` keeps a call alive when a provider refuses a parameter, and it does
so silently. An audit row that reported only the request could claim a control
the run never had. So this asks LiteLLM's own parameter mapping — the code that
does the dropping — which keeps the record and the wire from disagreeing. Where a
provider silently ignores a parameter LiteLLM forwards, as a gateway may, no local
record can see it; the mapping is the closest evidence there is.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from aaa.platform.model_registry.decoding.policy import decoding_kwargs

#: The decoding fields the record reports on.
_FIELDS = ("temperature", "seed")


@lru_cache(maxsize=64)
def _mapped(model: str, temperature: float | None,
            seed: int | None) -> tuple[tuple[str, Any], ...] | None:
    """LiteLLM's mapping of the request for *model*, or ``None`` if it has none.

    Cached: the mapping is a pure function of its arguments, and it runs on every
    audited call. Reached only once LiteLLM is known to import, so an import
    failure is never cached.
    """
    import litellm  # type: ignore  # pylint: disable=import-outside-toplevel
    from litellm.utils import (
        get_optional_params,  # type: ignore  # pylint: disable=import-outside-toplevel
    )

    try:
        name, provider, _, _ = litellm.get_llm_provider(model)
        params = get_optional_params(model=name, custom_llm_provider=provider,
                                     temperature=temperature, seed=seed, drop_params=True)
    except Exception:  # noqa: BLE001 - unmappable means "unknown", never a failed call
        return None
    return tuple((key, params[key]) for key in _FIELDS if key in params)


def sent_decoding(model: str) -> dict[str, Any] | None:
    """The decoding parameters LiteLLM will send for *model*.

    :param model: LiteLLM model string, provider prefix included.
    :returns: The subset of the request that survives the provider's parameter
        mapping, or ``None`` when LiteLLM cannot map the model or cannot be
        imported. An audit row must still be written in either case.
    """
    try:
        import litellm.utils  # type: ignore  # noqa: F401  # optional at import time
    except ImportError:
        return None
    requested = decoding_kwargs(model)
    mapped = _mapped(model, requested.get("temperature"), requested.get("seed"))
    return None if mapped is None else dict(mapped)


__all__ = ["sent_decoding"]
