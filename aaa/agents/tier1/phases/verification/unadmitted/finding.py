"""The one finding a phase raises for the artefacts the Verifier did not admit."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.phases.verification.unadmitted.records import _reason, clear_phase_finding
from aaa.platform.state.admission import artefact_verdict
from aaa.tools.findings import make_finding


def _record_finding(state: dict, unadmitted: list[str], articles: list[str], *,
                    phase_id: str, phase_label: str) -> None:
    """Raise (or refresh) this phase's one unadmitted-artefact finding."""
    finding_id = f"{phase_id or 'P?'}-VERIFY-UNADMITTED"
    findings: list[dict[str, Any]] = state.setdefault("blocking_findings", [])
    # A re-dispatched phase must not leave last dispatch's finding beside this
    # one; the finding describes the phase as it now stands.
    clear_phase_finding(state, finding_id)
    if not unadmitted:
        return
    critiques = state.get("verifier_critiques") or {}
    # The verdict *and* why: a reader of the finding has to be able to act on it
    # without opening the critique, which is the whole of Q1's complaint.
    named = "; ".join(
        f"{tid} ({(v := artefact_verdict(state, tid))} — "
        f"{_reason(critiques.get(tid) or {}, v)[:160]})" for tid in unadmitted)
    findings.append(make_finding(
        finding_id=finding_id,
        description=(
            f"{phase_label}: the independent Verifier did not admit {named}. The "
            f"artefact(s) are therefore not evidence, and the article(s) they were "
            f"accountable for are recorded INSUFFICIENT_EVIDENCE rather than assessed."),
        materiality="possibly_material",
        # The real articles, and none when only a report template was
        # unadmitted: the finding still reaches T18's findings section, and
        # inventing an article to hang it on would downgrade one the audit
        # did assess.
        articles=articles,
        source_phase=phase_id or phase_label,
        recommendation=("Have a human reviewer critique these artefacts, or obtain "
                        "the evidence they were to carry, before the report is signed."),
    ))


__all__ = ["_record_finding"]
