"""Whether the provider configured for a purpose can actually be called.

Two call sites used to gate on ``OPENAI_API_KEY`` directly, which was right
only while OpenAI was the one hosted provider. A local model needs no key, and
the OpenRouter provider needs a different one — so the question "can this
purpose embed?" is answered here, once, by the provider that owns it.
"""
from __future__ import annotations

import os

#: Hosted provider → the environment variable carrying its key.
_KEY_FOR: dict[str, str] = {"openai": "OPENAI_API_KEY", "openrouter": "OPENROUTER_API_KEY"}


def missing_credential(purpose: str) -> str | None:
    """Name the key the provider for *purpose* needs and does not have.

    :param purpose: One of :data:`aaa.platform.embeddings.PURPOSES`.
    :returns: An environment-variable name, or ``None`` when the provider can
        be called (a key is present, or none is needed).
    """
    from aaa.platform.embeddings.select import provider_for
    from aaa.settings import settings

    name = _KEY_FOR.get(provider_for(purpose))
    if name is None:
        return None
    if os.environ.get(name) or str(getattr(settings, name.lower(), "") or ""):
        return None
    return name


def credentials_present(purpose: str) -> bool:
    """True when embedding for *purpose* would not fail for want of a key.

    :param purpose: One of :data:`aaa.platform.embeddings.PURPOSES`.
    :returns: Whether the configured provider is callable.
    """
    return missing_credential(purpose) is None
