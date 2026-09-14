"""Adversarial probing of an LLM endpoint — or an honest statement that none ran.

``_run_garak`` used to return a hardcoded result: 150 probes, 2 successful
attacks, a 1.3 % vulnerability rate and a named finding, *"Leaked system prompt
via 'ignore instructions' variant."* It ignored ``target_uri`` entirely and
never raised, so the fallback below was unreachable and every engagement's T16
carried the same invented security finding — into the narrative the LLM writes,
into the client's report, and into ``derive_verdict``, which gates FAIL on that
rate. A fabricated adversarial test result in a conformity audit is the most
consequential form of the placeholder problem, so it is gone.

Nothing here manufactures a probe it did not run. Either garak is installed and
pointed at a reachable endpoint, or the result says ``tested: false`` and
carries the reason.
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

#: Patterns in a system prompt that weaken instruction-following. Used by the
#: static analysis, which reads a real artefact and is labelled as such.
_DANGEROUS_PATTERNS = re.compile(
    r"\b(ignore (?:all |any )?previous|disregard (?:all |any )?prior|"
    r"you are now|forget (?:everything|all)|developer mode)\b", re.IGNORECASE)


class InjectionProbeUnavailableError(RuntimeError):
    """Raised when adversarial probing cannot be performed."""


def not_tested(reason: str) -> dict[str, Any]:
    """The result shape for "no adversarial probing was performed".

    ``vulnerability_rate`` is ``None``, never ``0.0``: a zero reads as *probed
    and clean*, which is the opposite of what happened.

    :param reason: Why nothing was probed.
    :returns: The T16 ``prompt_injection_results`` shape, measured of nothing.
    """
    return {
        "tested": False,
        "method": "not_run",
        "not_tested_reason": reason,
        "total_probes": 0,
        "successful_attacks": 0,
        "vulnerability_rate": None,
        "attack_types": [],
        "critical_vulnerabilities": [],
        "observations": [],
    }


def _run_garak(target_uri: str | None) -> dict[str, Any]:
    """Red-team a live endpoint with garak.

    :param target_uri: The system under test's read-only API endpoint.
    :returns: Probe results.
    :raises InjectionProbeUnavailableError: When there is no endpoint to probe or
        garak is not installed. Never a stand-in result.
    """
    if not target_uri:
        raise InjectionProbeUnavailableError(
            "no read-only API endpoint was supplied for the system under test")
    try:  # pragma: no cover - exercised only where garak is installed
        import garak  # noqa: F401  # pyright: ignore[reportMissingImports]
    except ImportError as exc:
        raise InjectionProbeUnavailableError(
            "garak is not installed in this environment") from exc
    raise InjectionProbeUnavailableError(  # pragma: no cover
        "garak is installed but the probe runner is not wired up; no adversarial "
        "probing was performed")
