"""Which models refuse a sampling temperature: OpenAI's reasoning models.

OpenAI documents that its reasoning models — the o-series and the GPT-5 family —
accept only the default temperature, and its API rejects any other value. LiteLLM's
``drop_params`` is meant to absorb that, but what it knows is per version: 1.100.1
drops ``temperature`` for ``gpt-5.6-*``, while 1.86.0, the version this repository
pins, sends it. With the pin, every call on the default roster would be refused
and every agent would fall back to its deterministic path.

So the rule is applied here, from the vendor's documented behaviour, and LiteLLM is
asked only the two facts both versions agree on: which provider serves the model,
and whether the model reasons. Open-weight reasoning models served elsewhere,
MiniMax-M3 and Nemotron 3 among them, accept ``temperature=0`` and keep it.
"""
from __future__ import annotations

from functools import lru_cache

#: Providers that serve OpenAI's own models under OpenAI's parameter rules.
_OPENAI_HOSTS = frozenset({"openai", "azure"})


def refuses_temperature(model: str) -> bool:
    """Whether *model* is an OpenAI reasoning model, which takes no temperature.

    :param model: LiteLLM model string, provider prefix included.
    :returns: ``True`` only for a reasoning model on an OpenAI host; ``False``
        for everything else, including a model LiteLLM cannot resolve and a
        process where LiteLLM cannot be imported at all.
    """
    try:
        import litellm  # type: ignore  # noqa: F401  # optional at import time
    except ImportError:
        return False
    return bool(model) and _refuses(model)


@lru_cache(maxsize=128)
def _refuses(model: str) -> bool:
    """The cached lookup, reached only once LiteLLM is known to import.

    Kept apart so an import failure is never cached against a model name.
    """
    import litellm  # type: ignore  # pylint: disable=import-outside-toplevel

    try:
        _, provider, _, _ = litellm.get_llm_provider(model)
        return provider in _OPENAI_HOSTS and bool(litellm.supports_reasoning(model=model))
    except Exception:  # noqa: BLE001 - an unresolvable model keeps the default request
        return False


__all__ = ["refuses_temperature"]
