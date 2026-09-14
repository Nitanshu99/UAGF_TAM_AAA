"""Merges partner (S6/S7) article verdicts into the matrix, downgrade-only.

Partner evidence (``aaa.integrations``) may carry an explicit
``article_verdicts`` map, e.g. ``{"Art.13": "FAIL"}``. It can only ever
WORSEN an article's verdict — S5's own admitted evidence is the sole path to
PASS, so a partner (buggy, over-optimistic, or compromised) can never
promote a verdict, only flag a problem S5 missed. Absent ``article_verdicts``
this is a no-op — today's report-only behaviour.
"""
from __future__ import annotations

#: Verdict severity, worst → best is FAIL, INSUFFICIENT_EVIDENCE, PWO, PASS.
_SEVERITY = {"PASS": 0, "PASS_WITH_OBSERVATIONS": 1, "INSUFFICIENT_EVIDENCE": 2, "FAIL": 3}

#: Each partner may only propose a verdict for its own contractual article —
#: S6 (xai_evidence) → Art.13, S7 (security_evidence) → Art.15. Anything else
#: in their article_verdicts map is out of scope and ignored.
_PARTNER_SCOPE = {"xai_evidence": "Art.13", "security_evidence": "Art.15"}


def apply_partner_verdicts(state: dict, matrix: dict[str, str]) -> set[str]:
    """Downgrade *matrix* in place with any worse partner-proposed verdicts.

    :param state: The audit state (reads ``xai_evidence``/``security_evidence``).
    :type state: dict
    :param matrix: The compliance matrix, mutated in place.
    :type matrix: dict[str, str]
    :returns: Articles whose verdict changed (new row or downgrade) — the
        caller should refresh their evidence-entry rationale.
    :rtype: set[str]
    """
    changed: set[str] = set()
    for key, article in _PARTNER_SCOPE.items():
        evidence = state.get(key) or {}
        verdict = (evidence.get("article_verdicts") or {}).get(article)
        if verdict not in _SEVERITY:
            continue
        current = matrix.get(article)
        if current is None or _SEVERITY[verdict] > _SEVERITY.get(current, -1):
            matrix[article] = verdict
            changed.add(article)
    return changed
