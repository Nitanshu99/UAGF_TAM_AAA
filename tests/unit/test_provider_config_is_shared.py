"""CLI and UI must resolve the same model, from the same place.

The 2026-09-11 UI run was launched without ``OPENROUTER_MODEL`` /
``OPENROUTER_PROVIDER`` in its shell, because those had only ever been exported
inside a CLI wrapper script. It silently audited on ``nemotron-3-ultra:free``
while the CLI run beside it used ``minimax-m3`` — two runs of the same case, on
two different models, with nothing in either result saying so.

``aaa/__init__.py`` bootstraps the repo ``.env`` at package import, so every
entry point reads one config. These tests hold that: the roster must derive from
the environment rather than from whatever a launcher happened to export, and the
pin must never silently fall back.
"""
from __future__ import annotations

import subprocess
import sys

_RESOLVE = (
    "from aaa.platform.model_registry import get_model_config;"
    "c = get_model_config('Orchestrator');"
    "print(c.model, c.context_window)"
)


def _resolved(entry_import: str) -> tuple[str, str]:
    """Resolve the Orchestrator's model in a fresh interpreter.

    A subprocess is the point: the roster builds ``_ULTRA`` at import time, so
    only a clean process proves the value came from ``.env`` and not from an
    already-imported module in this one.

    :param entry_import: The entry point's own import line.
    :returns: ``(model, context_window)`` as printed by the child.
    """
    out = subprocess.run(
        [sys.executable, "-c", f"import {entry_import}\n{_RESOLVE}"],
        capture_output=True, text=True, check=True)
    model, window = out.stdout.strip().split()[-2:]
    return model, window


def test_cli_and_ui_resolve_the_same_model() -> None:
    """Two entry points, one configuration."""
    assert _resolved("aaa.cli") == _resolved("aaa.ui.app")


def test_the_package_import_is_what_loads_dotenv() -> None:
    """Importing anything under `aaa` must be enough to configure a run."""
    import aaa

    assert hasattr(aaa, "_bootstrap_dotenv")


def test_a_pinned_endpoint_never_falls_back(monkeypatch) -> None:
    """A pin that can silently be served elsewhere is not a pin.

    The token guard sizes budgets against the pinned endpoint's published
    window; being served a different one is the failure the pin exists to stop.
    """
    from aaa.platform.model_registry.openrouter.provider import provider_routing

    monkeypatch.setenv("OPENROUTER_MODEL", "minimax/minimax-m3")
    monkeypatch.setenv("OPENROUTER_PROVIDER", "coreweave/fp4")
    routing = provider_routing("openrouter/minimax/minimax-m3")
    assert routing["extra_body"]["provider"] == {
        "only": ["coreweave/fp4"], "allow_fallbacks": False}


def test_an_unpinned_model_selection_is_refused_not_guessed(monkeypatch) -> None:
    """`OPENROUTER_MODEL` alone must not appear to select a model (M19)."""
    from aaa.platform.model_registry.openrouter.provider import (
        DEFAULT_MODEL,
        pinned_endpoint,
        pinned_model,
    )

    monkeypatch.setenv("OPENROUTER_MODEL", "minimax/minimax-m3")
    monkeypatch.delenv("OPENROUTER_PROVIDER", raising=False)
    assert pinned_model() == "minimax/minimax-m3"
    assert pinned_endpoint() is None  # so the roster stays on the free route

    monkeypatch.setenv("OPENROUTER_MODEL", "not/a-real-model")
    assert pinned_model() == DEFAULT_MODEL
