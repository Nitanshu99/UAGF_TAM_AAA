"""Static analysis of a supplied system prompt, labelled as exactly that."""
from __future__ import annotations

from typing import Any

from aaa.tools.prompt_injection_suite.fallback import _run_fallback
from aaa.tools.prompt_injection_suite.probe import (  # noqa: F401
    _DANGEROUS_PATTERNS,
    InjectionProbeUnavailableError,
    _run_garak,
    logger,
    not_tested,
)


def prompt_injection_suite(
    target_uri: str | None = None,
    system_prompt: str | None = None,
) -> dict[str, Any]:
    """Probe an LLM endpoint adversarially, or say why nothing was probed.

    :param target_uri: URI of the system under test (API endpoint).
    :param system_prompt: The system prompt text, for static analysis.
    :returns: The T16 ``prompt_injection_results`` shape. ``tested`` and
        ``method`` say what actually happened; ``vulnerability_rate`` is
        ``None`` unless probes really ran.
    """
    try:
        return _run_garak(target_uri)
    except InjectionProbeUnavailableError as exc:
        logger.info("No adversarial probing (%s); reading the system prompt "
                    "statically instead.", exc)
        result = _run_fallback(system_prompt)
        result["not_tested_reason"] = (f"{exc}; " if result["method"] == "static_prompt_analysis"
                                       else "") + str(result.get("not_tested_reason") or exc)
        return result
