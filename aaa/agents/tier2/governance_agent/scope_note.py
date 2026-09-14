"""Say, in T14, which self-assessed articles this engagement does not assess.

The CGSA self-assessment maps its controls to the high-risk articles whatever the
system's tier. Case 02 (limited risk, 2026-09-13) carried that mapping into T14
unqualified and the Verifier refused it as citing obligations that do not apply.
The articles come from the payload's own compliance matrix, not from a list here.

The sentence states list membership, not law. It used to say the articles "do not
bind" the engagement; on case 06 that named Art. 16, 49 and 73 — high-risk provider
obligations the audit simply does not assess — and the Verifier twice refused T14,
asserting a contradiction with ``binding_articles`` (T-20260914-061). It now names that
field, which the Verifier holds and can check, and the verification gate reads the
sentence back to check a Verifier that disputes it (T-20260915-001).
"""
from __future__ import annotations

from typing import Any

from aaa.tools.regulatory_coverage.binding import binds, scope_known
from aaa.tools.regulatory_coverage.unbound_note import unbound_sentence


def _mapped_articles(payload: dict[str, Any]) -> list[str]:
    """``article_9`` … keys of the CGSA compliance matrix, as ``Art.9`` …."""
    matrix = payload.get("eu_ai_act_compliance_matrix") or {}
    return [f"Art.{key.split('_', 1)[1]}" for key in matrix if str(key).startswith("article_")]


def cgsa_scope_note(payload: dict[str, Any], scope: dict[str, Any]) -> str:
    """A sentence naming the mapped articles outside *scope*, or ``""``.

    :param payload: The validated CGSA payload.
    :param scope: ``{risk_tier, binding_articles}`` as dispatched to Phase 5 — the list the
        Verifier judges against — or a state-like dict with a tier.
    """
    if not scope_known(scope):
        return ""
    unbound = [a for a in _mapped_articles(payload) if not binds(scope, a)]
    return _tier_note(payload, scope) + ("" if not unbound else (
        f" Scope: this engagement's risk tier is '{scope.get('risk_tier')}'. "
        f"{unbound_sentence(unbound)}, so those mappings are recorded as "
        "governance practice and no verdict is given on them here."))


def _tier_note(payload: dict[str, Any], scope: dict[str, Any]) -> str:
    """Name the tier the self-assessment was made against when it is not the engagement's.

    Case 02's T14 carried ``cgsa_metadata.risk_tier: limited`` beside a verified
    'minimal' engagement, and the Verifier read the field as T14 asserting the tier
    (T-20260914-018). It is the assessment's own record and is kept as recorded.
    """
    declared = str((payload.get("metadata") or {}).get("risk_tier") or "").lower()
    engagement = str(scope.get("risk_tier") or "").lower()
    if not declared or declared == engagement:
        return ""
    return (f" The CGSA self-assessment was made against a '{declared}' risk tier; "
            "cgsa_metadata records that as the assessment's own statement, kept as recorded. "
            f"This engagement's verified tier is '{engagement}' (see risk_tier_match).")
