"""The comparisons a run must pass before it is worth paying for.

Each check answers one question: *if this run is dispatched now, will its result
be comparable with the reference run the case document pins?* A ``block`` means
the answer is no and the difference would be read as a finding rather than as a
configuration change — the failure mode that produced a softer audit on
2026-09-11 and was only noticed after the money was spent.
"""
from __future__ import annotations

import os
from typing import Any, NamedTuple

from aaa.tools.cgsa_pull.compat import describe, payload_profile
from aaa.tools.cgsa_pull.narrow import resolve_assessment_id


class Check(NamedTuple):
    """One preflight result."""

    name: str
    ok: bool
    blocking: bool
    detail: str


def check_model(reference: dict[str, Any]) -> Check:
    """Compare the model this process would use against the pinned one.

    :param reference: Parsed document header.
    :returns: The check result.
    """
    # Local import: the registry pulls the whole provider roster.
    from aaa.platform.model_registry.resolve import get_model_config

    want, pin = reference.get("model"), reference.get("provider_pin")
    # Any agent resolves the same provider default; Orchestrator is always
    # registered and is the first agent a run actually calls.
    got = get_model_config("Orchestrator").model
    got_pin = os.environ.get("OPENROUTER_PROVIDER") or None
    ok = (want is None or got == want) and (pin is None or got_pin == pin)
    return Check(
        "model", ok, True,
        f"pinned {want!r} / {pin!r}; this environment resolves {got!r} / {got_pin!r}",
    )


def check_cgsa(reference: dict[str, Any], state: dict[str, Any],
               organisation: str, system: str) -> Check:
    """Compare the CGSA this run would pull against the one the reference used.

    The dialect is the whole point. An evaluated export carries
    ``final_maturity_score`` and ``threshold_score`` on every control, so a
    control below its threshold becomes a material non-conformity; a
    self-assessment export carries neither, so no control can ever produce one
    and the articles that depend on it come back PASS or INSUFFICIENT_EVIDENCE.

    :param reference: Parsed document header.
    :param state: The reference run's AuditState.
    :param organisation: Provider name this run declares.
    :param system: System name this run declares.
    :returns: The check result.
    """
    from aaa.tools.cgsa_pull import CGSAPullError, cgsa_pull

    ref_profile = payload_profile(state.get("cgsa_payload") or {})
    assessment_id = resolve_assessment_id(organisation, system)
    if assessment_id is None:
        return Check("cgsa", False, True,
                     f"nothing resolves for {organisation!r} / {system!r}\n"
                     f"      reference used  — {describe(ref_profile)}")
    try:
        payload = cgsa_pull(assessment_id=assessment_id)
    except CGSAPullError as exc:
        return Check("cgsa", False, True,
                     f"{assessment_id} resolves but cannot be pulled ({exc.reason})")
    profile = payload_profile(payload)
    ok = profile["evaluated"] == ref_profile["evaluated"]
    return Check(
        "cgsa", ok, True,
        f"would pull {assessment_id} — {describe(profile)}\n"
        f"      reference used  — {describe(ref_profile)}",
    )
