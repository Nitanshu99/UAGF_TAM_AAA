"""State, in an artefact's ``artNN_compliance_notes``, when that article does not bind the engagement.

Case 02 (minimal-risk, clean loop 2026-09-13): T06 cited "Art. 10 §2–3" as the basis
of its examination although no article binds a minimal-risk system; the Verifier
ordered a rerun (T-20260913-092). The whole field family names an article as its
basis whatever the tier, so the note is added here, once, from the field name.
"""
from __future__ import annotations

import re
from typing import Any

from aaa.tools.regulatory_coverage.engagement_scope import is_in_scope, scope_is_known

_NOTE_FIELD = re.compile(r"^art(\d+)(?:_\w+)?_compliance_notes$")


def annotate_non_binding(artefact: dict[str, Any], risk_tier: str | None) -> None:
    """Append, in place, a scope sentence to each compliance note whose article does not bind.

    :param artefact: A phase artefact payload.
    :param risk_tier: The engagement's (verified) risk tier; unknown leaves notes untouched.
    """
    scope = {"risk_tier": risk_tier}
    if not scope_is_known(scope):
        return
    for field, value in list(artefact.items()):
        match = _NOTE_FIELD.match(field)
        if not match or not isinstance(value, str) or is_in_scope(scope, f"Art.{match.group(1)}"):
            continue
        artefact[field] = (f"{value.rstrip()} Art. {match.group(1)} does not bind this "
                           f"'{risk_tier}' engagement: this section records a voluntary "
                           "examination (Art. 95), not compliance with that article.")
