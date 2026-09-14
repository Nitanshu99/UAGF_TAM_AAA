"""T-20260914-011: the TruLens groundedness provider judges on the run's own model route.

``LiteLLM()`` defaulted to OpenAI's engine; with no OpenAI key every call failed
"Missing credentials" and groundedness was never measured on the free route.
"""
from __future__ import annotations

import sys
import types

from aaa.platform.model_registry.resolve import resolve_model
from aaa.tools.groundedness_check import groundedness_check


def test_the_provider_is_built_on_the_l_branch_roster_model(monkeypatch) -> None:
    """The engine TruLens is handed is the UAGF-TAM-L model under the active provider."""
    monkeypatch.setenv("PROVIDER", "openrouter")
    engines: list[str] = []

    class _Provider:
        def __init__(self, model_engine: str) -> None:
            engines.append(model_engine)

        def groundedness_measure_with_cot_reasons(self, _context, _answer):
            """Score as a provider would."""
            return 0.9, "supported"

    module = types.ModuleType("trulens.providers.litellm")
    module.LiteLLM = _Provider  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "trulens.providers.litellm", module)
    result = groundedness_check("The sky is blue.", "The sky is blue.")
    assert result["computed"] is True
    assert engines == [resolve_model("UAGF-TAM-L")]
    assert engines[0].endswith(":free")
