"""The declaration and document checks a comparable run has to pass."""
from __future__ import annotations

from typing import Any

from aaa.tools.run_preflight.checks import Check


def _submission(state: dict[str, Any], stage: str) -> dict[str, Any]:
    """One stage of the reference run's client submission."""
    return (state.get("client_submission") or {}).get(stage) or {}
def check_declaration(state: dict[str, Any], stage_a: dict[str, Any]) -> Check:
    """Compare the Stage A declaration against the reference run's.

    :param state: The reference run's AuditState.
    :param stage_a: The Stage A payload this run would submit.
    :returns: The check result.
    """
    reference = _submission(state, "stage_a")
    # `cgsa_assessment_id` is excluded deliberately: it is now derived rather
    # than declared, and the reference declared an id that did not match the
    # payload S4 actually served.
    keys = (set(reference) | set(stage_a)) - {"cgsa_assessment_id", "art43_preview"}
    differing = sorted(k for k in keys if reference.get(k) != stage_a.get(k))
    return Check(
        "declaration", not differing, False,
        "identical to the reference" if not differing
        else "differs on " + ", ".join(
            f"{k} ({reference.get(k)!r} -> {stage_a.get(k)!r})"[:110] for k in differing),
    )
def check_documents(state: dict[str, Any], stage_b: dict[str, Any]) -> Check:
    """Compare which Stage B document slots are filled, not their URIs.

    :param state: The reference run's AuditState.
    :param stage_b: The Stage B payload this run would submit.
    :returns: The check result.
    """
    from aaa.agents.intake_validator.errors import _CLIENT_DOC_URI_FIELDS

    reference = _submission(state, "stage_b")
    ref_filled = {f for f in _CLIENT_DOC_URI_FIELDS if reference.get(f)}
    new_filled = {f for f in _CLIENT_DOC_URI_FIELDS if stage_b.get(f)}
    missing, extra = sorted(ref_filled - new_filled), sorted(new_filled - ref_filled)
    detail = "same document slots as the reference"
    if missing or extra:
        detail = (f"missing {missing}" if missing else "") + \
                 (" | " if missing and extra else "") + (f"extra {extra}" if extra else "")
    return Check("documents", not (missing or extra), False, detail)


__all__ = ["_submission", "check_declaration", "check_documents"]
