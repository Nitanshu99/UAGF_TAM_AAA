"""Every provider the switch can select must be isolated from the unit suite.

``conftest._CREDENTIAL_VARS`` is a deny-list of key names, and a deny-list only
holds while someone remembers to extend it. Nobody did when OpenRouter was
added: on 2026-09-09 `.env` moved to ``PROVIDER=openrouter`` and the unit suite
began issuing **live** LLM calls on that route — 17m30s against a normal 2m20s,
real quota spent, one test failing on a real reply. The fixture's own docstring
describes that exact failure as the thing it prevents.

This derives the requirement from :mod:`aaa.platform.model_registry.provider`
instead, so a provider added later fails here rather than silently in a run.
"""
from __future__ import annotations

import os

import pytest

from aaa.platform.model_registry.provider import _KNOWN
from tests.unit.conftest import _CREDENTIAL_VARS

#: The environment variable LiteLLM reads for each provider the switch knows.
#: ``openai`` is the fallback for anything unrecognised, so it is covered too.
_PROVIDER_KEYS: dict[str, tuple[str, ...]] = {
    "openai": ("OPENAI_API_KEY",),
    "nvidia": ("NVIDIA_API_KEY", "NVIDIA_NIM_API_KEY"),
    "openrouter": ("OPENROUTER_API_KEY",),
}


def test_the_switch_has_not_gained_a_provider_this_guard_does_not_know():
    """A new provider must be added to `_PROVIDER_KEYS` — and then blanked."""
    assert set(_KNOWN) == set(_PROVIDER_KEYS), (
        "a provider was added to the switch; name the key it reads here, then "
        "add that key to conftest._CREDENTIAL_VARS")


@pytest.mark.parametrize("provider", sorted(_PROVIDER_KEYS))
def test_every_provider_key_is_blanked_by_the_isolation_fixture(provider):
    """The deny-list must cover every route a roster can resolve through."""
    missing = [k for k in _PROVIDER_KEYS[provider] if k not in _CREDENTIAL_VARS]
    assert not missing, f"{provider} can reach the network via {missing}"


@pytest.mark.parametrize("key", sorted({k for ks in _PROVIDER_KEYS.values() for k in ks}))
def test_no_provider_key_holds_a_value_during_a_unit_test(key):
    """The end state the deny-list exists to produce, asserted directly."""
    assert not os.environ.get(key), f"{key} is live inside the unit suite"
