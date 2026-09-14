"""What an unadmitted artefact is recorded as, and why the Verifier did not admit it."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.phases.verification.logger import _REPORT_TIDS, _VERDICT_ORDER
from aaa.agents.tier1.verifier.issues import issue_text
from aaa.platform.state.admission import ADMITTED_VERDICTS, NOT_CRITIQUED, artefact_verdict

#: The verdicts that do not admit an artefact, derived rather than restated so a
#: sixth verdict cannot be added to ``_VERDICT_ORDER`` without landing here.
UNADMITTED_VERDICTS: frozenset[str] = frozenset(_VERDICT_ORDER) - ADMITTED_VERDICTS

#: What to tell a reader when the critique itself gives no reason.
_DEFAULT_REASONS: dict[str, str] = {
    "unverified": "the Verifier's critique did not run",
    "rerun": "the Verifier rejected the artefact and its reruns were exhausted",
    "escalate_hitl": "the Verifier escalated the artefact to human review",
    NOT_CRITIQUED: "the artefact was never critiqued",
}


def _reason(critique: dict, verdict: str) -> str:
    """Say why an artefact was not admitted, in the Verifier's own words if it gave any."""
    stated = critique.get("unverified_reason")
    issues = [text for text in
              (issue_text(i) for i in (critique.get("issues") or [])) if text]
    return str(stated or "; ".join(issues[:2])
               or _DEFAULT_REASONS.get(verdict, f"verdict '{verdict}'"))[:400]


def _entry(state: dict, tid: str, articles: list[str], *,
           phase_id: str, phase_label: str) -> dict[str, Any]:
    """One record of an unadmitted artefact, carrying the articles *it* held back."""
    verdict = artefact_verdict(state, tid)
    critique = (state.get("verifier_critiques") or {}).get(tid) or {}
    return {"phase_id": phase_id, "phase_label": phase_label, "template_id": tid,
            "verdict": verdict,
            "articles": [] if tid in _REPORT_TIDS else list(articles),
            "reason": _reason(critique, verdict)}


def _is_phase_entry(entry: dict, phase_id: str, tids: set[str]) -> bool:
    """Whether *entry* is this phase's own record of one of its own artefacts.

    Shared with fix 35's no-report gate: both write into ``unadmitted_artefacts``
    and both must rewrite — never append to — the phase's own record, so that a
    re-dispatch that delivers releases what the lost attempt held (Q8).
    """
    return entry.get("phase_id") == phase_id and entry.get("template_id") in tids


def clear_phase_finding(state: dict, finding_id: str) -> None:
    """Drop any earlier attempt's *finding_id*; the finding describes the phase now.

    Never creates the key: a phase with nothing to say must leave no trace at
    all, which is what ``state`` looks like for an engagement whose every
    artefact was admitted.
    """
    findings: list[dict[str, Any]] = state.get("blocking_findings") or []
    findings[:] = [f for f in findings if f.get("finding_id") != finding_id]


__all__ = ["UNADMITTED_VERDICTS", "_entry", "_is_phase_entry", "_reason",
           "clear_phase_finding"]
