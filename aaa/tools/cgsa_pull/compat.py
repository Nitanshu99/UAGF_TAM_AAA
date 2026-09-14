"""Is this CGSA payload one the audit can actually reason about?

Two CGSA dialects reach this system and they are not interchangeable:

* ``s5-aaa-adapter-v1.0`` — the **evaluated** export. Every control carries
  ``final_maturity_score`` and ``threshold_score``, so
  :mod:`aaa.tools.cgsa_ingest.s5.fields` can raise a material non-conformity
  wherever a control sits below its threshold, and the compliance matrix spans
  the full article set.
* ``1.0.0`` — the **self-assessment** export. Controls carry ``maturity_score``
  and prose only. There is no threshold to fall below, so no control can ever
  produce a finding.

Feeding the second where the first is expected does not fail: it *degrades
silently*. On 2026-09-11 a Mariposa run against a self-assessment export
returned PASS on Arts. 5, 11 and 14 and INSUFFICIENT_EVIDENCE on Arts. 12, 50
and 72, where the evaluated export had produced FAIL on all six — a materially
softer audit, from a payload that validated cleanly and logged nothing.

That is what this module exists to catch, **before** a run is dispatched rather
than after it has been paid for.
"""
from __future__ import annotations

from typing import Any

#: Present on every control of an evaluated export; absent from all of a
#: self-assessment one. These are the two fields the below-threshold rule in
#: ``cgsa_ingest.s5.fields.control_summary`` reads.
EVALUATION_FIELDS = ("final_maturity_score", "threshold_score")


def _controls(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Every control record in a payload, across all domains."""
    return [control
            for domain in (payload.get("domains") or [])
            if isinstance(domain, dict)
            for control in (domain.get("controls") or [])
            if isinstance(control, dict)]


def payload_profile(payload: dict[str, Any]) -> dict[str, Any]:
    """Describe what a CGSA payload can and cannot support.

    :param payload: A parsed CGSA payload.
    :returns: ``dialect``, ``controls``, ``evaluated_controls``,
        ``matrix_articles`` and ``evaluated`` — the last being ``True`` only
        when every control carries the fields the threshold rule needs.
    """
    controls = _controls(payload)
    evaluated = sum(1 for c in controls
                    if all(c.get(f) is not None for f in EVALUATION_FIELDS))
    matrix = payload.get("eu_ai_act_compliance_matrix")
    return {
        "dialect": payload.get("schema_version"),
        "controls": len(controls),
        "evaluated_controls": evaluated,
        "matrix_articles": len(matrix) if isinstance(matrix, (dict, list)) else 0,
        "evaluated": bool(controls) and evaluated == len(controls),
    }


def is_evaluated(payload: dict[str, Any]) -> bool:
    """Whether this payload can produce control-level non-conformities.

    :param payload: A parsed CGSA payload.
    :returns: ``True`` for an evaluated export, ``False`` for a
        self-assessment one (or anything without controls).
    """
    return bool(payload_profile(payload)["evaluated"])


def describe(profile: dict[str, Any]) -> str:
    """One line an auditor can read before authorising a run.

    :param profile: The output of :func:`payload_profile`.
    :returns: A sentence naming the kind of export and what it supports.
    """
    if profile["evaluated"]:
        return (f"evaluated export ({profile['dialect']}): "
                f"{profile['evaluated_controls']} of {profile['controls']} controls "
                f"scored against a threshold, {profile['matrix_articles']} articles "
                "in its compliance matrix — control-level non-conformities will "
                "be raised.")
    return (f"self-assessment export ({profile['dialect']}): "
            f"{profile['controls']} controls carry no threshold, "
            f"{profile['matrix_articles']} articles in its compliance matrix — "
            "no control can produce a non-conformity, so articles that depend on "
            "one will come back PASS or INSUFFICIENT_EVIDENCE.")
